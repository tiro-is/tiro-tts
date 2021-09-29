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
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Literal, NewType, Optional

from .phonemes import PhoneSeq, convert_ipa_to_xsampa, convert_xsampa_to_ipa

LangID = NewType("LangID", str)


def read_kaldi_lexicon(lex_path: Path) -> Dict[str, PhoneSeq]:
    """Read a Kaldi style lexicon."""
    # TODO(rkjaran): Support pronunciation variants, possibly with POS info
    lexicon: Dict[str, PhoneSeq] = dict()
    lex_has_probs = None
    with lex_path.open() as lex_f:
        for line in lex_f:
            fields = line.strip().split()
            # Probe first line for syntax
            if lex_has_probs is None:
                lex_has_probs = re.match(r"[0-1]\.[0-9]+", fields[1]) is not None
            word = fields[0]
            if lex_has_probs:
                pron = fields[2:]
            else:
                pron = fields[1:]
            lexicon[word] = pron
    return lexicon


class LexWord:
    """An entry in a pronunciation lexicon."""

    class Properties:
        """Various properties of the lexical entry.

        This is empty for now, but will allow for adding point-of-speech, regional and
        other language info which might have an effect on whether this entry is
        preferred over a different entry.
        """

        def __init__(self, *args):
            pass

        def __eq__(self, other: Any) -> bool:
            # TODO(rkjaran): Add implementation once we add properties
            return isinstance(other, LexWord.Properties)

    grapheme: str
    phoneme: PhoneSeq
    properties: Properties

    def __init__(
        self,
        grapheme: str,
        phoneme: PhoneSeq,
        properties: Optional[Properties] = None,
    ):
        self.grapheme = grapheme
        self.phoneme = phoneme
        self.properties = properties if properties else LexWord.Properties()

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, LexWord)
            and self.grapheme == other.grapheme
            and self.phoneme == other.phoneme
            and self.properties == other.properties
        )


class LexiconBase(ABC):
    @abstractmethod
    def insert(self, entry: LexWord) -> None:
        """Insert a new entry into to lexicon."""
        return NotImplemented

    @abstractmethod
    def get(
        self,
        grapheme: str,
        default: Optional[PhoneSeq] = None,
        properties: Optional[LexWord.Properties] = None,
    ) -> PhoneSeq:
        """Get the IPA phoneme for grapheme or default if it doesn't exist.

        Args:
          grapheme: The grapheme to look up.
          default: This PhoneSeq will be returned if grapheme is not
              found, defaults to an empty list.
          properties: Ignored for now.

        Returns:
          The PhoneSeq for grapheme if it exists in the lexicon,
          otherwise default.
        """
        return NotImplemented

    @abstractmethod
    def get_xsampa(
        self,
        grapheme: str,
        default: Optional[PhoneSeq] = None,
        properties: Optional[LexWord.Properties] = None,
    ) -> PhoneSeq:
        """Get the phoneme for grapheme as X-SAMPA or default if it doesn't exist.

        Args:
          grapheme: The grapheme to look up.
          default: This PhoneSeq will be returned if grapheme is not
              found, defaults to an empty list.
          properties: Ignored for now.

        Returns:
          The PhoneSeq for grapheme if it exists in the lexicon,
          otherwise default.
        """
        return NotImplemented


class SimpleInMemoryLexicon(LexiconBase):
    _lexicon: Dict[str, PhoneSeq]
    _native_alphabet: Literal["x-sampa", "ipa"]

    def __init__(self, lex_path: Path, alphabet: Literal["x-sampa", "ipa"]):
        self._lexicon = read_kaldi_lexicon(lex_path)
        self._native_alphabet = alphabet

    def insert(self, entry: LexWord) -> None:
        """Insert a new entry into to lexicon."""
        self._lexicon[entry.grapheme] = entry.phoneme

    def get(
        self,
        grapheme: str,
        default: Optional[PhoneSeq] = None,
        properties: Optional[LexWord.Properties] = None,
    ) -> PhoneSeq:
        """Get the IPA phoneme for grapheme or default if it doesn't exist.

        Args:
          grapheme: The grapheme to look up.
          default: This PhoneSeq will be returned if grapheme is not
              found, defaults to an empty list.
          properties: Ignored for now.

        Returns:
          The PhoneSeq for grapheme if it exists in the lexicon,
          otherwise default.
        """
        phoneme = self._lexicon.get(grapheme, [])
        if not phoneme:
            return default or []
        if self._native_alphabet != "ipa":
            phoneme = convert_xsampa_to_ipa(phoneme)
        return phoneme

    def get_xsampa(
        self,
        grapheme: str,
        default: Optional[PhoneSeq] = None,
        properties: Optional[LexWord.Properties] = None,
    ) -> PhoneSeq:
        """Get the phoneme for grapheme as X-SAMPA or default if it doesn't exist.

        Args:
          grapheme: The grapheme to look up.
          default: This PhoneSeq will be returned if grapheme is not
              found, defaults to an empty list.
          properties: Ignored for now.

        Returns:
          The PhoneSeq for grapheme if it exists in the lexicon,
          otherwise default.
        """
        phoneme = self._lexicon.get(grapheme, [])
        if not phoneme:
            return default or []
        if self._native_alphabet != "x-sampa":
            phoneme = convert_ipa_to_xsampa(phoneme)
        return phoneme
