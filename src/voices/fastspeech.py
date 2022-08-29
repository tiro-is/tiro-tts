# Copyright 2021-2022 Tiro ehf.
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
import sys
import typing
from pathlib import Path
from typing import Literal, Optional

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
from src.frontend.phonemes import Alphabet
from src.frontend.ssml import OldSSMLParser as SSMLParser
from src.frontend.words import ProsodyProps, preprocess_sentences
from src.utils.version import VersionedThing, hash_from_impl

from .utils import wavarray_to_pcm
from .voice_base import OutputFormat, VoiceBase, VoiceProperties

# TODO(rkjaran): Don't hardcode this. Remove it once we've refactored FastSpeech2Voice
#   into a more generic TorchScript voice
FASTSPEECH2_SYMBOLS = {
    "a": 64,
    "aː": 65,
    "ai": 66,
    "aiː": 67,
    "au": 68,
    "auː": 69,
    "c": 70,
    "ç": 71,
    "cʰ": 72,
    "ð": 73,
    "ei": 74,
    "eiː": 75,
    "ɛ": 76,
    "ɛː": 77,
    "f": 78,
    "ɣ": 79,
    "h": 80,
    "i": 81,
    "iː": 82,
    "ɪ": 83,
    "ɪː": 84,
    "j": 85,
    "k": 86,
    "kʰ": 87,
    "l": 88,
    "l̥": 89,
    "m": 90,
    "m̥": 91,
    "n": 92,
    "n̥": 93,
    "ɲ": 94,
    "ɲ̊": 95,
    "ŋ": 96,
    "ŋ̊": 97,
    "œ": 98,
    "œː": 99,
    "œy": 100,
    "œyː": 101,
    "ou": 102,
    "ouː": 103,
    "ɔ": 104,
    "ɔː": 105,
    "ɔi": 106,
    "p": 107,
    "pʰ": 108,
    "r": 109,
    "r̥": 110,
    "s": 111,
    "t": 112,
    "tʰ": 113,
    "u": 114,
    "uː": 115,
    "v": 116,
    "x": 117,
    "ʏ": 118,
    "ʏː": 119,
    "ʏi": 120,
    "θ": 121,
    "sp": 122,
    "spn": 123,
    "sil": 124,
}


class FastSpeech2Synthesizer(VersionedThing):
    """A synthesizer wrapper around Fastspeech2 using MelGAN as a vocoder."""

    _device: torch.device
    _melgan_model: torch.jit.RecursiveScriptModule
    _fs_model: torch.jit.RecursiveScriptModule
    _phonetizer: GraphemeToPhonemeTranslatorBase
    _normalizer: NormalizerBase
    _alphabet: Alphabet
    _version_hash: Optional[str] = None

    def __init__(
        self,
        melgan_vocoder_path: os.PathLike,
        fastspeech_model_path: os.PathLike,
        phonetizer: GraphemeToPhonemeTranslatorBase,
        normalizer: NormalizerBase,
        alphabet: Alphabet = "ipa",
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
            map_location=self._device,
        )
        self._fs_model = torch.jit.load(
            fastspeech_model_path,
            map_location=self._device,
        )
        self._phonetizer = phonetizer
        self._normalizer = normalizer
        self._alphabet = alphabet

    def _do_vocoder_pass(self, mel: torch.Tensor) -> torch.Tensor:
        """Perform a vocoder pass, returning int16 samples at 22050 Hz."""
        return self._melgan_model.inference(mel).to(torch.int16)

    def synthesize(
        self,
        text_string: str,
        ssml: bool = False,
        sample_rate=22050,
        output_format: Literal["json", "pcm", "mp3", "ogg_vorbis"] = "pcm",
        *,
        use_ffmpeg: bool = True,
    ) -> typing.Iterable[bytes]:
        """Synthesize 16 bit PCM samples or a stream of JSON speech marks.

        Args:
          text_string: Text to be synthesized, can contain embedded phoneme
                       strings in {}

          ssml: Whether text_string is SSML markup or not

          sample_rate: Sample rate of the returned PCM chunks

          output_format: The output format is either one of the audio formats or json
                         for speech marks

        Yields:
          bytes: PCM chunk of synthesized audio, or JSON encoded speech marks

        """
        # Segment to decrease latency and memory usage
        duration_time_offset = 0

        duration_control = 1.0
        pitch_control = 1.0
        energy_control = 1.0

        def phonetize_fn(*args, **kwargs):
            return self._phonetizer.translate_words(
                *args, **kwargs, alphabet=self._alphabet
            )

        ssml_reqs: typing.Dict = {"process_as_ssml": ssml, "alphabet": self._alphabet}

        for segment_words, phone_seq, phone_counts in preprocess_sentences(
            text_string, ssml_reqs, self._normalizer.normalize, phonetize_fn
        ):
            prosody = ffmpeg.Prosody()

            if ssml and isinstance(segment_words[0].ssml_props, ProsodyProps):
                ssml_props = segment_words[0].ssml_props
                prosody.rate = ssml_props.rate
                prosody.pitch = ssml_props.pitch
                prosody.volume = ssml_props.volume

            # TODO(rkjaran): This is a "workaround" for the models we're using which
            #   can't handle synthesizing pauses/silence.
            if len(segment_words) == 1 and segment_words[0].phone_sequence[0] in (
                "sp",
                "sil",
            ):
                continue

            text_seq = torch.tensor(
                [[FASTSPEECH2_SYMBOLS[phoneme] for phoneme in phone_seq]],
                dtype=torch.int64,
                device=self._device,
            )

            (
                mel_postnet,
                # Duration of each phoneme in log(millisec)
                log_duration_output,
            ) = self._fs_model.inference(
                text_seq,
                d_control=duration_control,
                p_control=pitch_control,
                e_control=energy_control,
            )

            if output_format == "json":
                # The model uses 10 ms as the unit (or, technically, log(dur*10ms))
                phone_durations = (
                    10 * torch.exp(log_duration_output.detach()[0].to(torch.float32))
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
                    segment_words[idx].start_time_milli = segment_duration_time_offset
                    segment_duration_time_offset += int(
                        dur
                        / (
                            segment_words[idx].ssml_props.rate  # type: ignore
                            if isinstance(segment_words[idx].ssml_props, ProsodyProps)
                            else 1
                        )
                    )

                for word in segment_words:
                    if word.is_spoken():
                        yield word.to_json().encode("utf-8") + b"\n"

                duration_time_offset += segment_duration_time_offset
            else:
                # 22050 Hz 16 bit linear PCM chunks
                wav = self._do_vocoder_pass(mel_postnet).numpy()
                chunk = wavarray_to_pcm(
                    wav, src_sample_rate=22050, dst_sample_rate=sample_rate
                )

                if use_ffmpeg:
                    yield ffmpeg.to_format(
                        out_format=output_format,
                        audio_content=chunk,
                        src_sample_rate=str(sample_rate),
                        sample_rate=str(sample_rate),
                        prosody=prosody,
                    )
                else:
                    yield chunk

    @property
    def version_hash(self) -> str:
        # TODO(rkjaran): We want to separate the normalizer and phonetizer hashes, so we
        #   need a "VersionedThing" with different semantics
        if not self._version_hash:
            self._version_hash = hash_from_impl(
                self.__class__,
                str(self._melgan_model.state_dict())
                + str(self._fs_model.state_dict())
                + self._normalizer.version_hash
                + self._phonetizer.version_hash,
            )
        return self._version_hash


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

    def _synthesize(self, text: str, ssml: bool, **kwargs) -> typing.Iterable[bytes]:
        if not self._is_valid(**kwargs):
            raise ValueError("Synthesize request not valid")

        return self._backend.synthesize(
            text,
            ssml=ssml,
            sample_rate=int(kwargs["SampleRate"]),
            output_format=kwargs["OutputFormat"],
            use_ffmpeg=current_app.config["USE_FFMPEG"],
        )

    def synthesize(
        self, text: str, ssml: bool = False, **kwargs
    ) -> typing.Iterable[bytes]:
        """Synthesize audio from a string of characters or SSML markup."""
        return self._synthesize(text=text, ssml=ssml, **kwargs)

    @property
    def properties(self) -> VoiceProperties:
        return self._properties

    @property
    def version_hash(self) -> str:
        return self._backend.version_hash


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
