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
from typing import Callable, Iterable, List, Tuple

import tokenizer

from src.frontend.lexicon import LangID
from src.frontend.phonemes import PhoneSeq


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
    ):
        self.original_symbol = original_symbol
        self.symbol = symbol
        self.phone_sequence = phone_sequence
        self.start_byte_offset = start_byte_offset
        self.end_byte_offset = end_byte_offset
        self.start_time_milli = start_time_milli

    def __repr__(self):
        return "<Word(original_symbol='{}', symbol='{}', phone_sequence={}, start_byte_offset={}, end_byte_offset={}, start_time_milli={})>".format(
            self.original_symbol,
            self.symbol,
            self.phone_sequence,
            self.start_byte_offset,
            self.end_byte_offset,
            self.start_time_milli,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Word) and (
            self.original_symbol == other.original_symbol
            and self.symbol == other.symbol
            and self.phone_sequence == other.phone_sequence
            and self.start_byte_offset == other.start_byte_offset
            and self.end_byte_offset == other.end_byte_offset
            and self.start_time_milli == other.start_time_milli
        )

    def is_spoken(self):
        return self.original_symbol not in tokenizer.definitions.PUNCTUATION

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
    words = list(translator_fn(normalize_fn(text_string), LangID("is-IS")))
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
