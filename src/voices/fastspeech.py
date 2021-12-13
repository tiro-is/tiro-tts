# Copyright 2021 Tiro ehf.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import os
import re
import string
import sys
import typing
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import resampy
import tokenizer
import torch
from flask import current_app

from proto.tiro.tts import voice_pb2
from src import ffmpeg
from src.frontend.grapheme_to_phoneme import GraphemeToPhonemeTranslatorBase
from src.frontend.lexicon import LangID, SimpleInMemoryLexicon
from src.frontend.normalization import (
    BasicNormalizer,
    GrammatekNormalizer,
    NormalizerBase,
)
from src.frontend.phonemes import IPA_XSAMPA_MAP, XSAMPA_IPA_MAP, align_ipa_from_xsampa
from src.frontend.words import WORD_SENTENCE_SEPARATOR, Word

from .voice_base import OutputFormat, VoiceBase, VoiceProperties

if True:  # noqa: E402
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lib/fastspeech"))
    from src.lib.fastspeech import hparams as hp
    from src.lib.fastspeech import utils
    from src.lib.fastspeech.align_phonemes import Aligner
    from src.lib.fastspeech.g2p_is import translate as g2p
    from src.lib.fastspeech.synthesize import get_FastSpeech2
    from src.lib.fastspeech.text import text_to_sequence


class SSMLParser(HTMLParser):
    _ALLOWED_TAGS = ["speak", "phoneme"]
    _first_tag_seen: bool
    _tags_queue: typing.List[str]
    _prepared_fastspeech_strings: typing.List[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._first_tag_seen = False
        self._tags_queue = []
        self._prepared_fastspeech_strings = []

    def _check_first_tag(self, tag):
        if not self._first_tag_seen:
            if tag != "speak":
                raise ValueError("Start tag is not <speak>")
            self._first_tag_seen = True

    def handle_starttag(self, tag, attrs):
        self._check_first_tag(tag)

        if tag not in SSMLParser._ALLOWED_TAGS:
            raise ValueError("Unsupported tag encountered: '{}'".format(tag))

        if tag == "phoneme":
            attrs_map = dict(attrs)
            if attrs_map.get("alphabet") != "x-sampa" or "ph" not in attrs_map:
                raise ValueError(
                    "'phoneme' tag has to have 'alphabet' and 'ph' attributes"
                )
            self._prepared_fastspeech_strings.append(
                "{%s}" % align_ipa_from_xsampa(attrs_map["ph"])
            )
        self._tags_queue.append(tag)

    def handle_endtag(self, tag):
        open_tag = self._tags_queue.pop()
        if open_tag != tag:
            raise ValueError("Invalid closing tag '{}' for '{}'".format(tag, open_tag))

    def handle_data(self, data):
        # Raise a ValueError if we haven't seen the initial <speak> tag
        self._check_first_tag("")

        if self._tags_queue[-1] != "phoneme":
            self._prepared_fastspeech_strings.append(data.strip())

    def get_fastspeech_string(self):
        return " ".join(self._prepared_fastspeech_strings)


class FastSpeech2Synthesizer:
    """A synthesizer wrapper around Fastspeech2 using MelGAN as a vocoder."""

    _device: torch.device
    _melgan_model: torch.jit.RecursiveScriptModule
    _fs_model: torch.jit.RecursiveScriptModule
    _phonetizer: GraphemeToPhonemeTranslatorBase
    _normalizer: NormalizerBase

    def __init__(
        self,
        melgan_vocoder_path: os.PathLike,
        fastspeech_model_path: os.PathLike,
        phonetizer: GraphemeToPhonemeTranslatorBase,
        normalizer: NormalizerBase,
    ):
        """Initialize a FastSpeech2Synthesizer.

        Args:
          melgan_vocoder_path: Path to the TorchScript MelGAN vocoder for this voice.
              See https://github.com/seungwonpark/melgan and the script
              melgan_convert.py.

          fastspeech_model_path: Path to the TorchScript fastspeech model for this.
              See https://github.com/cadia-lvl/FastSpeech2 and the script
              fastspeech_convert.py.

          phonetizer: A GraphemeToPhonemeTranslator to use for the input text.

          normalizer: A Normalizer used to normalize the input text prior to synthesis

        """
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._melgan_model = torch.jit.load(
            melgan_vocoder_path,
            map_location=self._device
        )
        self._fs_model = torch.jit.load(
            fastspeech_model_path,
            map_location=self._device
        )
        self._phonetizer = phonetizer
        self._normalizer = normalizer
        self._max_words_per_segment = 30

    def _add_phonemes(self, words: typing.Iterable[Word]) -> typing.Iterable[Word]:
        for word in words:
            if not word == WORD_SENTENCE_SEPARATOR:
                # TODO(rkjaran): Cover more punctuation (Unicode)
                punctuation = re.sub(r"[{}\[\]]", "", string.punctuation)
                g2p_word = re.sub(r"([{}])".format(punctuation), r" \1 ", word.symbol)
                # TODO(rkjaran): The language code shouldn't be hardcoded here. Should
                #                it be here at all?
                word.phone_sequence = self._phonetizer.translate(
                    g2p_word, LangID("is-IS")
                )
            yield word

    def _melgan_inference(self, mel: torch.Tensor) -> torch.Tensor:
        hop_length = 256
        n_mel_channels = (
            80  # this number (from hparams) is hardcoded for now, unlikely to change
        )
        max_wav_value = 32768.0

        # pad input mel with zeros to cut artifact
        # see https://github.com/seungwonpark/melgan/issues/8
        zero = torch.full((1, n_mel_channels, 10), -11.5129).to(mel.device)
        mel = torch.cat((mel, zero), dim=2)

        audio = self._melgan_model(mel)
        audio = audio.squeeze()  # collapse all dimension except time axis
        audio = audio[: -(hop_length * 10)]
        audio = max_wav_value * audio
        audio = audio.clamp(min=-max_wav_value, max=max_wav_value - 1)
        audio = audio.short()

        return audio

    def _do_vocoder_pass(self, mel_postnet: torch.Tensor) -> torch.Tensor:
        """Perform a vocoder pass, returning int16 samples at 22050 Hz."""
        mel_postnet_torch = mel_postnet.transpose(1, 2).detach()
        with torch.no_grad():
            wav = self._melgan_inference(mel_postnet_torch).cpu()
            return (wav * (20000 / torch.max(torch.abs(wav)))).to(torch.int16)

    @staticmethod
    def _wavarray_to_pcm(
        array: np.ndarray, src_sample_rate=22050, dst_sample_rate=22050
    ) -> bytes:
        """Convert a NDArray (int16) to a PCM byte chunk, resampling if necessary."""

        def to_pcm_bytes(array1d):
            return array1d.view("b").data.tobytes()

        if sys.byteorder == "big":
            array.byteswap()

        orig_samples = array.ravel()
        if src_sample_rate == dst_sample_rate:
            return to_pcm_bytes(orig_samples)
        return to_pcm_bytes(
            resampy.resample(orig_samples, src_sample_rate, dst_sample_rate)
        )

    def synthesize(
        self,
        text_string: str,
        emit_speech_marks=False,
        sample_rate=22050,
        # TODO(rkjaran): remove once we support normalization with SSML in a generic
        #   way. Also remove it from FastSpeech2Voice
        handle_embedded_phonemes=False,
    ) -> typing.Iterable[bytes]:
        """Synthesize 16 bit PCM samples or a stream of JSON speech marks.

        Args:
          text_string: Text to be synthesized, can contain embedded phoneme
                       strings in {}

          emit_speech_marks: Whether to generate speech marks or PCM samples

          sample_rate: Sample rate of the returned PCM chunks

        Yields:
          bytes: PCM chunk of synthesized audio, or JSON encoded speech marks
        """
        duration_control = 1.0
        pitch_control = 1.0
        energy_control = 1.0

        # TODO(rkjaran): remove conditional once we remove the
        #   `handle_embedded_phonemes` argument
        normalize_fn = (
            self._normalizer.normalize
            if not handle_embedded_phonemes
            else BasicNormalizer().normalize
        )
        words = list(self._add_phonemes(normalize_fn(text_string)))
        sentences: typing.List[typing.List[Word]] = [[]]
        for idx, word in enumerate(words):
            if word == WORD_SENTENCE_SEPARATOR:
                if idx != len(words) - 1:
                    sentences.append([])
            else:
                sentences[-1].append(word)

        # Segment to decrease latency and memory usage
        duration_time_offset = 0
        for sentence in sentences:
            for idx in range(0, len(sentence), self._max_words_per_segment):
                segment_words = sentence[idx : idx + self._max_words_per_segment]

                phone_counts: typing.List[int] = []
                phone_seq = []

                for word in segment_words:
                    phone_counts.append(len(word.phone_sequence))
                    phone_seq.extend(word.phone_sequence)

                if not phone_seq:
                    # If none of the words in this segment got a phone sequence we skip the
                    # rest
                    continue

                text_seq = torch.tensor(
                    [text_to_sequence("{%s}" % " ".join(phone_seq), hp.text_cleaners)],
                    dtype=torch.int64,
                    device=self._device,
                )
                src_len = torch.tensor([text_seq.shape[1]], device=self._device)

                (
                    mel,
                    mel_postnet,
                    # Duration of each phoneme in log(millisec)
                    log_duration_output,
                    f0_output,
                    energy_output,
                    src_mask,
                    mel_mask,
                    mel_len,
                ) = self._fs_model(
                    text_seq,
                    src_len,
                    d_control=duration_control,
                    p_control=pitch_control,
                    e_control=energy_control,
                )

                if emit_speech_marks:
                    # The model uses 10 ms as the unit (or, technically, log(dur*10ms))
                    phone_durations = (
                        10
                        * torch.exp(log_duration_output.detach()[0].to(torch.float32))
                    ).tolist()
                    word_durations = []
                    offset = 0
                    for count in phone_counts:
                        word_durations.append(
                            # type: ignore
                            sum(phone_durations[offset : offset + count])
                        )
                        offset += count

                    segment_duration_time_offset: int = duration_time_offset
                    for idx, dur in enumerate(word_durations):
                        segment_words[
                            idx
                        ].start_time_milli = segment_duration_time_offset
                        segment_duration_time_offset += dur

                    for word in segment_words:
                        if word.is_spoken():
                            yield word.to_json().encode("utf-8") + b"\n"

                    duration_time_offset += segment_duration_time_offset
                else:
                    # 22050 Hz 16 bit linear PCM chunks
                    wav = self._do_vocoder_pass(mel_postnet).numpy()
                    yield FastSpeech2Synthesizer._wavarray_to_pcm(
                        wav, src_sample_rate=22050, dst_sample_rate=sample_rate
                    )


class FastSpeech2Voice(VoiceBase):
    _backend: FastSpeech2Synthesizer
    _properties: VoiceProperties

    def __init__(self, properties: VoiceProperties, backend):
        """Initialize a fixed voice with a FastSpeech2 backend."""
        self._backend = backend
        self._properties = properties

    def _is_valid(self, **kwargs) -> bool:
        # Some sanity checks
        try:
            return (
                kwargs["OutputFormat"] in ("pcm", "ogg_vorbis", "mp3", "json")
                and kwargs["VoiceId"] == self._properties.voice_id
                and "Text" in kwargs
            )
        except KeyError:
            return False

    def _synthesize(
        self, text: str, handle_embedded_phonemes=False, **kwargs
    ) -> typing.Iterable[bytes]:
        if not self._is_valid(**kwargs):
            raise ValueError("Synthesize request not valid")

        for chunk in self._backend.synthesize(
            text,
            emit_speech_marks=kwargs["OutputFormat"] == "json",
            sample_rate=int(kwargs["SampleRate"]),
            handle_embedded_phonemes=handle_embedded_phonemes,
        ):
            if current_app.config["USE_FFMPEG"]:
                if kwargs["OutputFormat"] == "ogg_vorbis":
                    yield ffmpeg.to_ogg_vorbis(
                        chunk,
                        src_sample_rate=kwargs["SampleRate"],
                        sample_rate=kwargs["SampleRate"],
                    )
                elif kwargs["OutputFormat"] == "mp3":
                    yield ffmpeg.to_mp3(
                        chunk,
                        src_sample_rate=kwargs["SampleRate"],
                        sample_rate=kwargs["SampleRate"],
                    )
            if kwargs["OutputFormat"] in ("pcm", "json"):
                yield chunk

    def synthesize(self, text: str, **kwargs) -> typing.Iterable[bytes]:
        """Synthesize audio from a string of characters."""
        return self._synthesize(text, **kwargs)

    def synthesize_from_ssml(self, ssml: str, **kwargs) -> typing.Iterable[bytes]:
        """Synthesize audio from SSML markup."""
        # TODO(rkjaran): Move SSML parser out of here and make it more general
        parser = SSMLParser()
        parser.feed(ssml)
        text = parser.get_fastspeech_string()
        parser.close()
        return self._synthesize(text=text, handle_embedded_phonemes=True, **kwargs)

    @property
    def properties(self) -> VoiceProperties:
        return self._properties


_OGG_VORBIS_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_MP3_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_PCM_SAMPLE_RATES = ["8000", "16000", "22050"]
SUPPORTED_OUTPUT_FORMATS = [
    OutputFormat(output_format="pcm", supported_sample_rates=_PCM_SAMPLE_RATES),
    OutputFormat(
        output_format="ogg_vorbis", supported_sample_rates=_OGG_VORBIS_SAMPLE_RATES
    ),
    OutputFormat(output_format="mp3", supported_sample_rates=_MP3_SAMPLE_RATES),
    OutputFormat(output_format="json", supported_sample_rates=[]),
]
