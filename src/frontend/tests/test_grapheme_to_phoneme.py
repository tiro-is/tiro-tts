from pathlib import Path
from pytest import raises

from ..grapheme_to_phoneme import       \
SequiturGraphemeToPhonemeTranslator,    \
LexiconGraphemeToPhonemeTranslator

from ..lexicon import SimpleInMemoryLexicon

def phoneseq_to_str(seq: "list[str]"):
    return "".join(seq)

class TestLexiconGraphemeToPhonemeTranslator:
    _language_code: str = "is-IS"
    _lex_path: Path = Path("external/test_models/lexicon.txt")
    _alphabet: str = "x-sampa"
    _t: LexiconGraphemeToPhonemeTranslator = LexiconGraphemeToPhonemeTranslator(
        { 
            _language_code: SimpleInMemoryLexicon(
                lex_path=_lex_path,
                alphabet=_alphabet
            )
        }
    )

    def translate_to_str(self, text: str):
        res: str = phoneseq_to_str(self._t.translate(text, self._language_code))
        print(f"Lex: {text} => {res}")
        return res

    def test_one_empty(self):
        text: str = ""
        assert self.translate_to_str(text) == ""

class TestSequiturGraphemeToPhonemeTranslator:
    _model_path: Path = Path("external/test_models/sequitur.mdl")
    _language_code: str = "is-IS"
    _t: SequiturGraphemeToPhonemeTranslator = SequiturGraphemeToPhonemeTranslator(
        lang_model_paths={ 
            _language_code: _model_path
        }
    )

    def translate_to_str(self, text: str):
        res: str = phoneseq_to_str(self._t.translate(text, self._language_code))
        return res

    def test_one_empty(self):
        text: str = ""
        assert self.translate_to_str(text) == ""

    def test_two_multiword(self):
        text: str = "Halló heimur"
        assert self.translate_to_str(text) == "halouheiːmʏr"

    def test_three_incorrect_data_type(self):
        text: int = 15
        with raises(AttributeError):
            self.translate_to_str(text)

    def test_four_word_lower_case_01(self):
        text = "kleprar"
        assert self.translate_to_str(text) == "kʰlɛːprar"

    def test_five_word_lower_case_02(self):
        text = "blöðrupumpur"
        assert self.translate_to_str(text) == "plœðrʏpʰʏm̥pʏr"

    def test_six_word_capital_first(self):
        text = "Blöðrupumpur"
        assert self.translate_to_str(text) == "plœðrʏpʰʏm̥pʏr"

    def test_seven_word_all_caps(self):
        text = "FJANDSAMLEGUR"
        assert self.translate_to_str(text) == "fjantsamlɛɣʏr"