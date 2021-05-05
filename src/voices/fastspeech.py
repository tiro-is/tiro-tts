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
import os
import sys
import io
import json
import re
import typing
from typing import BinaryIO
import string
import torch
import numpy as np
from flask import current_app
from html.parser import HTMLParser
from . import VoiceBase, VoiceProperties, OutputFormat
import ffmpeg

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lib/fastspeech"))
from lib.fastspeech.synthesize import get_FastSpeech2, load_g2p
from lib.fastspeech.g2p_is import translate as g2p
from lib.fastspeech import utils, hparams as hp
from lib.fastspeech.text import text_to_sequence
from lib.fastspeech.align_phonemes import Aligner
from scipy.io import wavfile
from .phonemes import XSAMPA_IPA_MAP, IPA_XSAMPA_MAP


def _align_ipa_from_xsampa(phoneme_string: str):
    return " ".join(
        XSAMPA_IPA_MAP[phn]
        for phn in Aligner(phoneme_set=set(XSAMPA_IPA_MAP.keys()))
        .align(phoneme_string.replace(" ", ""))
        .split(" ")
    )


def _align_ipa(phoneme_string: str):
    return " ".join(
        phn
        for phn in Aligner(phoneme_set=set(IPA_XSAMPA_MAP.keys()))
        .align(phoneme_string.replace(" ", ""))
        .split(" ")
    )


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
                "{%s}" % _align_ipa_from_xsampa(attrs_map["ph"])
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


MELGAN_VOCODER_PATH = current_app.config["MELGAN_VOCODER_PATH"]
FASTSPEECH_MODEL_PATH = current_app.config["FASTSPEECH_MODEL_PATH"]
SEQUITUR_MODEL_PATH = current_app.config["SEQUITUR_MODEL_PATH"]


class Word:
    def __init__(
        self,
        original_symbol: str = "",
        symbol: str = "",
        phone_sequence: typing.List[str] = [],
        start_byte_offset: int = 0,
        end_byte_offset: int = 0,
        start_time_milli: int = 0,
    ):
        self.original_symbol = original_symbol
        self.symbol = symbol
        self.phone_sequence = phone_sequence
        self.start_byte_offset = start_byte_offset
        self.end_byte_offset = end_byte_offset
        self.start_time_milli = start_time_milli

    def to_json(self):
        return json.dumps(
            {
                "time": self.start_time_milli,
                "type": "word",
                "start": self.start_byte_offset,
                "end": self.end_byte_offset,
                "value": self.original_symbol,
            },
            ensure_ascii=False,
        )


class FastSpeech2Synthesizer:
    def __init__(
        self,
        melgan_vocoder_path: str = MELGAN_VOCODER_PATH,
        fastspeech_model_path: str = FASTSPEECH_MODEL_PATH,
        sequitur_model_path: str = SEQUITUR_MODEL_PATH,
    ):
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._melgan_model = utils.get_melgan(full_path=melgan_vocoder_path)
        self._melgan_model.to(self._device)
        self._fs_model = get_FastSpeech2(490000, full_path=fastspeech_model_path)
        self._fs_model.to(self._device)
        self._g2p_model = load_g2p(sequitur_model_path)

    def _word_offsets(self, text: str) -> typing.List[typing.List[int]]:
        """Returns the start and end offsets of each whitespace separated token in
        `text`

        NOTE: This doesn't work with SSML input

        """
        start_end_pairs = [[]]
        text_bytes = text.encode("utf-8")
        skippable_chars = string.whitespace.encode("utf-8")
        for offset, b in enumerate(text_bytes):
            if b in skippable_chars:
                continue

            if len(start_end_pairs[-1]) == 2:
                start_end_pairs.append([])

            if len(start_end_pairs[-1]) == 0:
                start_end_pairs[-1].append(offset)

            if (
                offset + 1 == len(text_bytes)
                or text_bytes[offset + 1] in skippable_chars
            ):
                start_end_pairs[-1].append(offset + 1)

        return start_end_pairs

    def _tokenize(self, text: str) -> typing.Iterable[Word]:
        # TODO(rkjaran): Very simple "tokenization". Replace once a better
        #                frontend processor is ready.

        # Split on whitespace into words except for blocks of phonemes (enclosed
        # in {}), keeping punctuation attached
        current_word_segments = []
        phoneme_str_open = False
        for w, offsets in zip(text.split(), self._word_offsets(text)):
            if phoneme_str_open:
                current_word_segments.append(w)
                if w.endswith("}"):
                    yield Word(
                        symbol="".join(current_word_segments),
                        start_byte_offset=offsets[0],
                        end_byte_offset=offsets[1],
                    )
                    phoneme_str_open = False
                    current_word_segments = []
            elif not phoneme_str_open:
                if w.startswith("{") and not w.endswith("}"):
                    current_word_segments.append(w)
                    phoneme_str_open = True
                else:
                    yield Word(
                        original_symbol=w,
                        symbol=w,
                        start_byte_offset=offsets[0],
                        end_byte_offset=offsets[1],
                    )

    def _add_phonemes(self, words: typing.Iterable[Word]) -> typing.Iterable[Word]:
        for word in words:
            punctuation = re.sub(r"[{}\[\]]", "", string.punctuation)
            g2p_word = re.sub(r"([{}])".format(punctuation), r" \1 ", word.symbol)
            word.phone_sequence = g2p(g2p_word, self._g2p_model)
            yield word

    def synthesize(
        self, text_string: str, file_obj: BinaryIO, emit_speech_marks=False
    ) -> None:
        """Surround phoneme strings with {}"""
        duration_control = 1.0
        pitch_control = 1.0
        energy_control = 1.0

        # Keep track of the phonemes in each word so we'll be able to map the
        # phoneme durations to word time alignment
        words = list(self._add_phonemes(self._tokenize(text_string)))
        phone_counts: typing.List[int] = []
        phone_seq = []

        for word in words:
            phone_counts.append(len(word.phone_sequence))
            phone_seq.extend(word.phone_sequence)

        sequence = np.array(
            text_to_sequence("{%s}" % " ".join(phone_seq), hp.text_cleaners)
        )
        sequence = np.stack([sequence])
        text_seq = torch.from_numpy(sequence).long().to(self._device)
        src_len = torch.from_numpy(np.array([text_seq.shape[1]])).to(self._device)

        (
            mel,
            mel_postnet,
            log_duration_output,  # Duration of each phoneme in log(millisec)
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
            phone_durations = np.exp(log_duration_output.detach().numpy()[0])
            word_durations = []
            offset = 0
            for count in phone_counts:
                word_durations.append(
                    round(sum(phone_durations[offset : offset + count]))  # type: ignore
                )
                offset += count

            for idx, dur in enumerate(word_durations):
                words[idx].start_time_milli = dur

            for word in words:
                file_obj.write(word.to_json().encode("utf-8"))
                file_obj.write(b"\n")
        else:
            mel_postnet_torch = mel_postnet.transpose(1, 2).detach()
            mel = mel[0].cpu().transpose(0, 1).detach()
            mel_postnet = mel_postnet[0].cpu().transpose(0, 1).detach()
            f0_output = f0_output[0].detach().cpu().numpy()
            energy_output = energy_output[0].detach().cpu().numpy()

            with torch.no_grad():
                wav = self._melgan_model.inference(mel_postnet_torch).cpu().numpy()

            wav = (wav * (20000 / np.max(np.abs(wav)))).astype("int16")
            wavfile.write(file_obj, hp.sampling_rate, wav)


class FastSpeech2Voice(VoiceBase):
    _backend: FastSpeech2Synthesizer
    _properties: VoiceProperties

    def __init__(self, properties: VoiceProperties, backend=None):
        """Initialize a fixed voice with a FastSpeech2 backend"""
        self._backend = backend if backend else FastSpeech2Synthesizer()
        self._properties = properties

    def _is_valid(self, **kwargs) -> bool:
        # Some sanity checks
        try:
            return (
                kwargs["OutputFormat"] in ("pcm", "ogg_vorbis", "mp3", "json")
                and not (
                    kwargs["OutputFormat"] == "pcm" and kwargs["SampleRate"] != "22050"
                )
                and kwargs["VoiceId"] == self._properties.voice_id
                and "Text" in kwargs
            )
        except KeyError:
            return False

    def synthesize(self, text: str, **kwargs) -> bytes:
        # TODO(rkjaran): chunk the content
        if not self._is_valid(**kwargs):
            raise ValueError("Synthesize request not valid")

        content = io.BytesIO()
        self._backend.synthesize(
            text, content, emit_speech_marks=kwargs["OutputFormat"] == "json"
        )

        if current_app.config["USE_FFMPEG"]:
            if kwargs["OutputFormat"] == "ogg_vorbis":
                return ffmpeg.to_ogg_vorbis(
                    content.getvalue(), sample_rate=kwargs["SampleRate"]
                )
            elif kwargs["OutputFormat"] == "mp3":
                return ffmpeg.to_mp3(
                    content.getvalue(), sample_rate=kwargs["SampleRate"]
                )

        return content.getvalue()

    def synthesize_from_ssml(self, ssml: str, **kwargs) -> bytes:
        parser = SSMLParser()
        parser.feed(ssml)
        text = parser.get_fastspeech_string()
        parser.close()
        return self.synthesize(text=text, **kwargs)

    @property
    def properties(self) -> VoiceProperties:
        return self._properties


_OGG_VORBIS_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_MP3_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_PCM_SAMPLE_RATES = ["22050"]
_SUPPORTED_OUTPUT_FORMATS = [
    OutputFormat(output_format="pcm", supported_sample_rates=_PCM_SAMPLE_RATES),
    OutputFormat(
        output_format="ogg_vorbis", supported_sample_rates=_OGG_VORBIS_SAMPLE_RATES
    ),
    OutputFormat(output_format="mp3", supported_sample_rates=_MP3_SAMPLE_RATES),
    OutputFormat(output_format="json", supported_sample_rates=[]),
]

# List of all available fastspeech voices
VOICES = [
    VoiceProperties(
        voice_id="Bjartur",
        name="Other",
        gender="Male",
        language_code="is-IS",
        language_name="Íslenska",
        supported_output_formats=_SUPPORTED_OUTPUT_FORMATS,
    ),
    VoiceProperties(
        voice_id="Other",
        name="Other",
        gender="Male",
        language_code="is-IS",
        language_name="Íslenska",
        supported_output_formats=_SUPPORTED_OUTPUT_FORMATS,
    )
]
