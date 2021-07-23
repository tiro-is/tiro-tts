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

import ffmpeg

from .grapheme_to_phoneme import SequiturGraphemeToPhonemeTranslator
from .lexicon import LangID, SimpleInMemoryLexicon
from .phonemes import IPA_XSAMPA_MAP, XSAMPA_IPA_MAP
from .voice_base import OutputFormat, VoiceBase, VoiceProperties

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lib/fastspeech"))
if True:  # noqa: E402
    from lib.fastspeech.synthesize import get_FastSpeech2
    from lib.fastspeech.g2p_is import translate as g2p
    from lib.fastspeech import utils, hparams as hp
    from lib.fastspeech.text import text_to_sequence
    from lib.fastspeech.align_phonemes import Aligner


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
LEXICON_PATH = current_app.config["LEXICON_PATH"]
SEQUITUR_FAIL_EN_MODEL_PATH = current_app.config["SEQUITUR_FAIL_EN_MODEL_PATH"]


class Word:
    """A wrapper for individual symbol and its metadata."""

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
        """Serialize Word to JSON."""
        return json.dumps(
            {
                "time": round(self.start_time_milli),
                "type": "word",
                "start": self.start_byte_offset,
                "end": self.end_byte_offset,
                "value": self.original_symbol,
            },
            ensure_ascii=False,
        )


# Use an empty initialized word as a sentence separator
WORD_SENTENCE_SEPARATOR = Word()


class FastSpeech2Synthesizer:
    """A synthesizer wrapper around Fastspeech2 using MelGAN as a vocoder."""

    def __init__(
        self,
        melgan_vocoder_path: str = MELGAN_VOCODER_PATH,
        fastspeech_model_path: str = FASTSPEECH_MODEL_PATH,
        sequitur_model_path: str = SEQUITUR_MODEL_PATH,
        lexicon_path: str = LEXICON_PATH,
        sequitur_fail_en_model_path: str = SEQUITUR_FAIL_EN_MODEL_PATH,
        language_code: str = "is-IS",
    ):
        """Initialize a FastSpeech2Synthesizer.

        Args:
          melgan_vocoder_path: Path to the MelGAN vocoder for this voice.
              See https://github.com/seungwonpark/melgan.

          fastspeech_model_path: Path to the fastspeech model for this.
              See https://github.com/cadia-lvl/FastSpeech2.

          sequitur_model_path: Path to a Sequitur G2P model that uses the correct
              phoneset (see `lib.fastspeech.text.cmudict.valid_symbols`).

          lexicon_path: Path to a pronuncation lexicon for looking up symbols prior to
              performing G2P. *NOTE*: This is currently assumed to be in X-SAMPA
              compatible with the Sequitur phoneset (see `voices.phonemes`).

          sequitur_fail_en_model_path: Path to a sequitur G2P model using the
              same phoneset as `sequitur_model_path`. This is assumed to be en-US
              and used when both the lexicon lookup and primary G2P translation fail.

          language_code: The primary language code for the voice.
        """
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._melgan_model = utils.get_melgan(full_path=melgan_vocoder_path)
        self._melgan_model.to(self._device)
        self._fs_model = get_FastSpeech2(None, full_path=fastspeech_model_path)
        self._fs_model.to(self._device)

        # TODO(rkjaran): Move the lang codes to a parameter, possibly when we define a
        #                proper config structure
        lang_model_paths = {LangID(language_code): Path(sequitur_model_path)}
        if sequitur_fail_en_model_path:
            lang_model_paths.update(
                {LangID("en-IS"): Path(sequitur_fail_en_model_path)}
            )
        self._phonetisizer = SequiturGraphemeToPhonemeTranslator(
            lang_model_paths=lang_model_paths,
            lexica={
                LangID(language_code): SimpleInMemoryLexicon(
                    Path(lexicon_path), alphabet="x-sampa"
                )
            }
            if lexicon_path
            else {},
        )

        self._max_words_per_segment = 30

    def _tokenize(self, text: str) -> typing.Iterable[Word]:
        """Split input into spoken tokens.

        Args:
          text: Input text to be tokenized.

        Yields:
          Word: spoken word symbols, including their *byte* offsets in `text`.  A
            default initialized Word represents a sentence boundary.

        """
        # TODO(rkjaran): This doesn't handle embedded phonemes properly, but the
        #                previous version didn't either.
        tokens = list(tokenizer.tokenize_without_annotation(text))

        def utf8_byte_length(string: str) -> int:
            return len(string.encode("utf-8"))

        def is_token_spoken(
            token: tokenizer.Tok,
        ) -> bool:
            return token.kind != tokenizer.TOK.PUNCTUATION or not token.original

        def add_token_offsets(
            tokens: typing.Iterable[tokenizer.Tok],
        ) -> typing.List[typing.Tuple[tokenizer.Tok, int, int]]:
            # can't throw away sentence end/start info
            n_bytes_consumed: int = 0
            byte_offsets: typing.List[typing.Tuple[tokenizer.Tok, int, int]] = []
            for tok in tokens:
                if tok.kind == tokenizer.TOK.S_END:
                    byte_offsets.append((tok, 0, 0))
                    continue
                if not tok.origin_spans or not tok.original:
                    continue
                if is_token_spoken(tok):
                    start_offset = n_bytes_consumed + utf8_byte_length(
                        tok.original[: tok.origin_spans[0]]
                    )
                    end_offset = start_offset + utf8_byte_length(
                        tok.original[tok.origin_spans[0] : tok.origin_spans[-1] + 1]
                    )

                    byte_offsets.append((tok, start_offset, end_offset))
                n_bytes_consumed += utf8_byte_length(tok.original)
            return byte_offsets

        current_word_segments = []
        phoneme_str_open = False
        for tok, start_byte_offset, end_byte_offset in add_token_offsets(tokens):
            if tok.kind == tokenizer.TOK.S_END:
                yield WORD_SENTENCE_SEPARATOR
                continue

            w = typing.cast(str, tok.original).strip()
            if phoneme_str_open:
                current_word_segments.append(w)
                if w.endswith("}"):
                    yield Word(
                        original_symbol="".join(current_word_segments),
                        symbol="".join(current_word_segments),
                        start_byte_offset=start_byte_offset,
                        end_byte_offset=end_byte_offset,
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
                        start_byte_offset=start_byte_offset,
                        end_byte_offset=end_byte_offset,
                    )

    def _add_phonemes(self, words: typing.Iterable[Word]) -> typing.Iterable[Word]:
        for word in words:
            if not word == WORD_SENTENCE_SEPARATOR:
                punctuation = re.sub(r"[{}\[\]]", "", string.punctuation)
                g2p_word = re.sub(r"([{}])".format(punctuation), r" \1 ", word.symbol)
                word.phone_sequence = self._phonetisizer.translate(
                    g2p_word, LangID("is-IS"), failure_langs=(LangID("en-IS"),)
                )
            yield word

    def _do_vocoder_pass(self, mel_postnet: torch.Tensor) -> torch.Tensor:
        """Perform a vocoder pass, returning int16 samples at 22050 Hz."""
        mel_postnet_torch = mel_postnet.transpose(1, 2).detach()
        with torch.no_grad():
            wav = self._melgan_model.inference(mel_postnet_torch).cpu()
            return (wav * (20000 / torch.max(torch.abs(wav)))).to(torch.int16)

    @staticmethod
    def _wavarray_to_pcm(
        array: np.array, src_sample_rate=22050, dst_sample_rate=22050
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
        self, text_string: str, emit_speech_marks=False, sample_rate=22050
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

        # Keep track of the phonemes in each word so we'll be able to map the
        # phoneme durations to word time alignment
        words = list(self._add_phonemes(self._tokenize(text_string)))

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

    def __init__(self, properties: VoiceProperties, backend=None):
        """Initialize a fixed voice with a FastSpeech2 backend."""
        self._backend = backend if backend else FastSpeech2Synthesizer()
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

    def synthesize(self, text: str, **kwargs) -> typing.Iterable[bytes]:
        """Synthesize audio from a string of characters."""
        if not self._is_valid(**kwargs):
            raise ValueError("Synthesize request not valid")

        for chunk in self._backend.synthesize(
            text,
            emit_speech_marks=kwargs["OutputFormat"] == "json",
            sample_rate=int(kwargs["SampleRate"]),
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

    def synthesize_from_ssml(self, ssml: str, **kwargs) -> typing.Iterable[bytes]:
        """Synthesize audio from SSML markup."""
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
_PCM_SAMPLE_RATES = ["8000", "16000", "22050"]
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
        voice_id="Alfur",
        name="Álfur",
        gender="Male",
        language_code="is-IS",
        language_name="Íslenska",
        supported_output_formats=_SUPPORTED_OUTPUT_FORMATS,
    ),
]
