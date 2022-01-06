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

    def test_one_empty(self):
        text: str = ""
        assert self._t.translate(text, self._language_code) == []

    def test_two_multiword(self):
        text: str = "Halló heimur"
        assert self._t.translate(text, self._language_code) == ['h', 'a', 't', 'l', 'ou', 'h', 'eiː', 'm', 'ʏ', 'r']

    def test_three_incorrect_data_type(self):
        text: int = 15
        with raises(AttributeError):
            self._t.translate(text, self._language_code)

    def test_four_word_lower_01(self):
        text = "stormur"
        assert self._t.translate(text, self._language_code) == ['s', 't', 'ɔ', 'r', 'm', 'ʏ', 'r']

    def test_five_word_lower_02(self):
        text = "varnarmálaráðherra"
        assert self._t.translate(text, self._language_code) \
            == ['v', 'a', 'r', 't', 'n', 'a',
                'r', 'm', 'au', 'l', 'a', 'r',
                'au', 'θ', 'h', 'ɛ', 'r', 'a']

    def test_six_word_nonexistant_01(self):
        text = "kleprar"
        assert self._t.translate(text, self._language_code) == []

    def test_seven_word_nonexistant_02(self):
        text = "blöðrupumpur"
        assert self._t.translate(text, self._language_code) == []

    def test_eight_foreign_char_01(self):
        text = "Султан"
        assert self._t.translate(text, self._language_code) == []

    def test_nine_foreign_char_02(self):
        text = "дlvдrlegt"
        assert self._t.translate(text, self._language_code) == []

    def test_ten_sentence(self):
        text = "ekki voru allir á sama máli um hvað ætti að gera við Vigfús"
        assert self._t.translate(text, self._language_code)   \
            == ['ɛ', 'h', 'c', 'ɪ', 'v', 'ɔː',
                'r', 'ʏ', 'a', 't', 'l', 'ɪ',
                'r', 'auː', 's', 'aː', 'm', 'a',
                'm', 'auː', 'l', 'ɪ', 'kʰ', 'v',
                'aː', 'ð', 'ai', 'h', 't', 'ɪ',
                'c', 'ɛː', 'r', 'a', 'v', 'ɪː',
                'ð', 'v', 'ɪ', 'x', 'f', 'u', 
                's']

    def test_eleven_sentence_punctuated(self):
        text = "Flestum þótti Vigfús vera ómerkilegur, enda með eindæmum venjulegur í framkomu."
        assert self._t.translate(text, self._language_code)   \
            == ['f', 'l', 'ɛ', 's', 't', 'ʏ',
                'm', 'θ', 'ou', 'h', 't', 'ɪ',
                'v', 'ɪ', 'x', 'f', 'u', 's',
                'v', 'ɛː', 'r', 'a', 'ouː', 'm',
                'ɛ', 'r̥', 'c', 'ɪ', 'l', 'ɛ',
                'ɣ', 'ʏ', 'r', 'sp', 'ɛ', 'n',
                't', 'a', 'm', 'ɛː', 'ð', 'ei',
                'n', 't', 'ai', 'm', 'ʏ', 'm',
                'v', 'ɛ', 'n', 'j', 'ʏ', 'l',
                'ɛ', 'ɣ', 'ʏ', 'r', 'iː', 'f',
                'r', 'a', 'm', 'kʰ', 'ɔ', 'm',
                'ʏ', 'sp']

class TestSequiturGraphemeToPhonemeTranslator:
    _model_path: Path = Path("external/test_models/sequitur.mdl")
    _language_code: str = "is-IS"
    _t: SequiturGraphemeToPhonemeTranslator = SequiturGraphemeToPhonemeTranslator(
        lang_model_paths={ 
            _language_code: _model_path
        }
    )

    def translate_to_str(self, text: str) -> str:
        return phoneseq_to_str(self._t.translate(text, self._language_code))

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

    def test_four_word_lower_01(self):
        text = "kleprar"
        assert self.translate_to_str(text) == "kʰlɛːprar"

    def test_five_word_lower_02(self):
        text = "blöðrupumpur"
        assert self.translate_to_str(text) == "plœðrʏpʰʏm̥pʏr"

    def test_six_word_capital_first(self):
        text = "Blöðrupumpur"
        assert self.translate_to_str(text) == "plœðrʏpʰʏm̥pʏr"

    def test_seven_word_all_caps(self):
        text = "FJANDSAMLEGUR"
        assert self.translate_to_str(text) == "fjantsamlɛɣʏr"

    def test_eight_foreign_char_01(self):
        text = "Султан"
        assert self.translate_to_str(text) == ""

    def test_nine_foreign_char_02(self):
        text = "дlvдrlegt"
        assert self.translate_to_str(text) == ""