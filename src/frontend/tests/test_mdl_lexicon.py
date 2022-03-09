from pathlib import Path
from typing import Literal

from ..lexicon import LexWord, SimpleInMemoryLexicon
from ..phonemes import PhoneSeq


class TestSimpleInMemoryLexicon:
    _lex_path: Path = Path("external/test_models/lexicon.txt")
    _alphabet: Literal["x-sampa"] = "x-sampa"

    _lexicon: SimpleInMemoryLexicon = SimpleInMemoryLexicon(
        lex_path=_lex_path, alphabet=_alphabet
    )

    # === get (ipa) tests start here ===

    def test_get_empty(self):
        assert self._lexicon.get("") == []

    def test_get_grapheme_nonexistant_01(self):
        assert self._lexicon.get("dvergasúpa") == []

    def test_get_grapheme_nonexistant_02(self):
        assert self._lexicon.get("airplane") == []

    def test_get_graphemes_multiple(self):
        assert self._lexicon.get("maður og kona") == []

    def test_get_symbol_01(self):
        assert self._lexicon.get("#") == []

    def test_get_symbol_02(self):
        assert self._lexicon.get(",") == []

    def test_get_int_str(self):
        assert self._lexicon.get("42") == []

    def test_get_incorrect_type(self):
        assert self._lexicon.get(42) == []

    def test_get_grapheme_01(self):
        assert self._lexicon.get("útlendingastofnun") == [
            "uː",
            "t",
            "l",
            "ɛ",
            "n",
            "t",
            "i",
            "ŋ",
            "k",
            "a",
            "s",
            "t",
            "ɔ",
            "p",
            "n",
            "ʏ",
            "n",
        ]

    def test_get_grapheme_02(self):
        assert self._lexicon.get("bollaleggingar") == [
            "p",
            "ɔ",
            "t",
            "l",
            "a",
            "l",
            "ɛ",
            "c",
            "i",
            "ŋ",
            "k",
            "a",
            "r",
        ]

    def test_get_grapheme_03(self):
        assert self._lexicon.get("pöbb") == ["pʰ", "œ", "p"]

    def test_get_grapheme_04(self):
        assert self._lexicon.get("verðmætasköpun") == [
            "v",
            "ɛ",
            "r",
            "ð",
            "m",
            "ai",
            "t",
            "a",
            "s",
            "k",
            "œ",
            "p",
            "ʏ",
            "n",
        ]

    def test_get_grapheme_05(self):
        assert self._lexicon.get("þýskaland") == [
            "θ",
            "i",
            "s",
            "k",
            "a",
            "l",
            "a",
            "n",
            "t",
        ]

    def test_get_grapheme_06(self):
        assert self._lexicon.get("dauðarefsing") == [
            "t",
            "œyː",
            "ð",
            "a",
            "r",
            "ɛ",
            "f",
            "s",
            "i",
            "ŋ",
            "k",
        ]

    # === get_xsampa tests start here ===

    def test_get_xsampa_empty(self):
        assert self._lexicon.get_xsampa("") == []

    def test_get_xsampa_grapheme_nonexistant_01(self):
        assert self._lexicon.get_xsampa("dvergasúpa") == []

    def test_get_xsampa_grapheme_nonexistant_02(self):
        assert self._lexicon.get_xsampa("airplane") == []

    def test_get_xsampa_graphemes_multiple(self):
        assert self._lexicon.get_xsampa("maður og kona") == []

    def test_get_xsampa_symbol_01(self):
        assert self._lexicon.get_xsampa("#") == []

    def test_get_xsampa_symbol_02(self):
        assert self._lexicon.get_xsampa(",") == []

    def test_get_xsampa_int_str(self):
        assert self._lexicon.get_xsampa("42") == []

    def test_get_xsampa_incorrect_type(self):
        assert self._lexicon.get_xsampa(42) == []

    def test_get_xsampa_grapheme_01(self):
        assert self._lexicon.get_xsampa("útlendingastofnun") == [
            "u:",
            "t",
            "l",
            "E",
            "n",
            "t",
            "i",
            "N",
            "k",
            "a",
            "s",
            "t",
            "O",
            "p",
            "n",
            "Y",
            "n",
        ]

    def test_get_xsampa_grapheme_02(self):
        assert self._lexicon.get_xsampa("bollaleggingar") == [
            "p",
            "O",
            "t",
            "l",
            "a",
            "l",
            "E",
            "c",
            "i",
            "N",
            "k",
            "a",
            "r",
        ]

    def test_get_xsampa_grapheme_03(self):
        assert self._lexicon.get_xsampa("pöbb") == ["p_h", "9", "p"]

    def test_get_xsampa_grapheme_04(self):
        assert self._lexicon.get_xsampa("verðmætasköpun") == [
            "v",
            "E",
            "r",
            "D",
            "m",
            "ai",
            "t",
            "a",
            "s",
            "k",
            "9",
            "p",
            "Y",
            "n",
        ]

    def test_get_xsampa_grapheme_05(self):
        assert self._lexicon.get_xsampa("þýskaland") == [
            "T",
            "i",
            "s",
            "k",
            "a",
            "l",
            "a",
            "n",
            "t",
        ]

    def test_get_xsampa_grapheme_06(self):
        assert self._lexicon.get_xsampa("dauðarefsing") == [
            "t",
            "9i:",
            "D",
            "a",
            "r",
            "E",
            "f",
            "s",
            "i",
            "N",
            "k",
        ]

    # === insert tests ===

    def test_insert_01(self):
        insertion_grapheme: str = "leet"
        insertion_phoneme: PhoneSeq = ["1337"]

        assert self._lexicon.get_xsampa(insertion_grapheme) == []
        self._lexicon.insert(
            LexWord(grapheme=insertion_grapheme, phoneme=insertion_phoneme)
        )
        assert self._lexicon.get_xsampa(insertion_grapheme) == insertion_phoneme

    def test_insert_02(self):
        insertion_grapheme: str = "bolabítur"
        insertion_phoneme: PhoneSeq = ["b0l4b33tur"]

        assert self._lexicon.get_xsampa(insertion_grapheme) == []
        self._lexicon.insert(
            LexWord(grapheme=insertion_grapheme, phoneme=insertion_phoneme)
        )
        assert self._lexicon.get_xsampa(insertion_grapheme) == insertion_phoneme

    def test_insert_already_exists(self):
        insertion_grapheme: str = "fótanudd"
        insertion_phoneme: PhoneSeq = ["fódanut"]

        # Assert that the entry exists
        assert self._lexicon.get_xsampa(insertion_grapheme) != []

        self._lexicon.insert(
            LexWord(grapheme=insertion_grapheme, phoneme=insertion_phoneme)
        )

        # Assert that the insertion overwrote the existing entry
        assert self._lexicon.get_xsampa(insertion_grapheme) == insertion_phoneme
