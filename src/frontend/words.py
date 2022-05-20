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
from typing import Callable, Dict, Iterable, List, Literal, Tuple

import tokenizer

from src.frontend.lexicon import LangID
from src.frontend.phonemes import (
    ALIGNER_XSAMPA,
    ALIGNER_XSAMPA_SYLL_STRESS,
    align_ipa_from_xsampa,
    PhoneSeq,
)


class SSMLProps:
    tag_type: Literal["speak", "phoneme", "sub"] = ""
    tag_val: str
    data: str = ""

    def __init__(self):
        ...

    def get_data(self):
        return self.data

    def is_multi(self, alternate_data: str = None) -> bool:
        data = alternate_data if alternate_data else self.data
        return len(data.split()) > 1

class SpeakProps(SSMLProps):
    def __init__(
        self,
        tag_val: str,
        data: str = "",
    ):
        self.tag_type = "speak"
        self.tag_val = tag_val
        self.data = data

    def __repr__(self):
        return "<SpeakProps(tag_type='{}', tag_val='{}', data='{}')>".format(
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SpeakProps) and (
            self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class PhonemeProps(SSMLProps):
    read: bool

    def __init__(
        self,
        tag_val: str,
        alphabet: Literal["x-sampa", "ipa"] = "",
        ph: str = "",
        data: str = "",
    ):
        self.tag_val = tag_val
        self.alphabet = alphabet
        self.ph = ph
        self.tag_type = "phoneme"
        self.data = data
        self.read = False

    def get_phone_sequence(
        self, alphabet: Literal["ipa", "x-sampa", "x-sampa+syll+stress"]
    ) -> List[str]:
        if alphabet not in ["ipa", "x-sampa", "x-sampa+syll+stress"]:
            raise ValueError("Illegal alphabet choice: {}".format(alphabet))

        if not self.read:
            self.read = True

            # SSML markup only allows x-sampa phone sequences in the phoneme tags. Some models,
            # like Fastspeech, only accept IPA phone sequences and, therefore, this function
            # offers conversion from x-sampa to IPA if required.

            try:
                # If alignment fails, the phone sequence (ph) is illegal.
                if alphabet == "ipa":
                    return align_ipa_from_xsampa(self.ph).split()
                if alphabet == "x-sampa":
                    return ALIGNER_XSAMPA.align(self.ph).split()
                if alphabet == "x-sampa+syll+stress":
                    return ALIGNER_XSAMPA_SYLL_STRESS.align(self.ph).split()
            except Exception as e:
                raise ValueError(
                    "<phoneme> error: Illegal phoneme sequence in 'ph' attribute\n{}".format(
                        e
                    )
                )
        return []

    def __repr__(self):
        return (
            "<PhonemeProps(alphabet='{}', ph='{}', tag_type='{}', tag_val='{}', data='{}')>".format(
                self.alphabet,
                self.ph,
                self.tag_type,
                self.tag_val,
                self.data,
            )
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PhonemeProps) and (
            self.alphabet == other.alphabet
            and self.ph == other.ph
            and self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class SubProps(SSMLProps):
    def __init__(
        self,
        tag_val: str,
        data: str,
        alias: str,
    ):
        self.tag_val = tag_val
        self.alias = alias
        self.tag_type = "sub"
        self.data = data

    def get_alias(self):
        return self.alias

    def __repr__(self):
        return "<SubProps(alias='{}', tag_type='{}', tag_val='{}', data='{}')>".format(
            self.alias,
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SubProps) and (
            self.alias == other.alias
            and self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )

class Word:
    """A wrapper for individual symbol and its metadata."""

    def __init__(
        self,
        original_symbol: str = "",
        symbol: str = "",
        phone_sequence: List[str] = [],
        start_byte_offset: int = 0,
        end_byte_offset: int = 0,
        start_time_milli: int = 0,
        ssml_props: SSMLProps = None,
    ):
        self.original_symbol = original_symbol
        self.symbol = symbol
        self.phone_sequence = phone_sequence
        self.start_byte_offset = start_byte_offset
        self.end_byte_offset = end_byte_offset
        self.start_time_milli = start_time_milli
        self.ssml_props = ssml_props

    def __repr__(self):
        return "<Word(original_symbol='{}', symbol='{}', phone_sequence={}, start_byte_offset={}, end_byte_offset={}, start_time_milli={}, ssml_props={})>".format(
            self.original_symbol,
            self.symbol,
            self.phone_sequence,
            self.start_byte_offset,
            self.end_byte_offset,
            self.start_time_milli,
            self.ssml_props,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Word) and (
            self.original_symbol == other.original_symbol
            and self.symbol == other.symbol
            and self.phone_sequence == other.phone_sequence
            and self.start_byte_offset == other.start_byte_offset
            and self.end_byte_offset == other.end_byte_offset
            and self.start_time_milli == other.start_time_milli
            # and self.ssml_props == other.ssml_props
        )

    def is_spoken(self):
        return self.original_symbol not in tokenizer.definitions.PUNCTUATION

    def is_from_ssml(self):
        return self.ssml_props != None

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


MAX_WORDS_PER_SEGMENT = 30


def preprocess_sentences(
    text_string: str,
    ssml_reqs: Dict,
    normalize_fn: Callable[[str], Iterable[Word]],
    translator_fn: Callable[[Iterable[Word]], Iterable[Word]],
) -> Iterable[Tuple[List[List[Word]], PhoneSeq, List[int]]]:
    """Preprocess text into sentences of phonetized words

    Yields:
      A tuple (List[Word], PhoneSeq, List[int]) of the words in the segment, a flattened
        phoneme sequence of each segment and list of phoneme counts per word in the
        segment.

    """
    # TODO(rkjaran): The language code shouldn't be hardcoded here.
    words = list(translator_fn(normalize_fn(text_string, ssml_reqs), LangID("is-IS")))
    sentences: List[List[Word]] = [[]]
    for idx, word in enumerate(words):
        if word == WORD_SENTENCE_SEPARATOR:
            if idx != len(words) - 1:
                sentences.append([])
        else:
            sentences[-1].append(word)

    for sentence in sentences:
        for idx in range(0, len(sentence), MAX_WORDS_PER_SEGMENT):
            segment_words = sentence[idx : idx + MAX_WORDS_PER_SEGMENT]

            phone_counts: List[int] = []
            phone_seq = []

            for word in segment_words:
                phone_counts.append(len(word.phone_sequence))
                phone_seq.extend(word.phone_sequence)

            if not phone_seq:
                # If none of the words in this segment got a phone sequence we skip the
                # rest
                continue

            yield segment_words, phone_seq, phone_counts
