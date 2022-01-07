from pathlib import Path
from pytest import raises

from ..grapheme_to_phoneme import       \
ComposedTranslator,                     \
SequiturGraphemeToPhonemeTranslator,    \
LexiconGraphemeToPhonemeTranslator

from ..lexicon import SimpleInMemoryLexicon

class TestComposedTranslator:
    _language_code: str = "is-IS"
    _alphabet: str = "x-sampa"
    _lex_path: Path = Path("external/test_models/lexicon.txt")
    _model_path: Path = Path("external/test_models/sequitur.mdl")

    _lexiconGraphemeToPhonemeTranslator: LexiconGraphemeToPhonemeTranslator = LexiconGraphemeToPhonemeTranslator(
        {
            _language_code: SimpleInMemoryLexicon(
                lex_path=_lex_path,
                alphabet=_alphabet
            )
        }
    )

    _sequiturGraphemeToPhonemeTranslator: SequiturGraphemeToPhonemeTranslator = SequiturGraphemeToPhonemeTranslator(
        lang_model_paths={ 
            _language_code: _model_path
        }
    )

    _t = ComposedTranslator(_lexiconGraphemeToPhonemeTranslator, _sequiturGraphemeToPhonemeTranslator)

    def test_empty(self):
        text: str = ""
        assert self._t.translate(text, self._language_code) == []

    def test_multiword(self):
        text: str = "Halló heimur"
        assert self._t.translate(text, self._language_code) == ['h', 'a', 't', 'l', 'ou', 'h', 'eiː', 'm', 'ʏ', 'r']

    # LexiconGraphemeToPhonemeTranslator can not handle these test cases but SequiturGraphemeToPhonemeTranslator can,
    # thus the latter should handle them.
    def test_word_sequitur_01(self):
        text = "kleprar"
        assert self._t.translate(text, self._language_code) == ['kʰ', 'l', 'ɛː', 'p', 'r', 'a', 'r']

    def test_word_sequitur_02(self):
        text = "Blöðrupumpur"
        assert self._t.translate(text, self._language_code) == ['p', 'l', 'œ', 'ð', 'r', 'ʏ', 'pʰ', 'ʏ', 'm̥', 'p', 'ʏ', 'r']

    def test_word_sequitur_03(self):
        text = "FJANDSAMLEGUR"
        assert self._t.translate(text, self._language_code) == ['f', 'j', 'a', 'n', 't', 's', 'a', 'm', 'l', 'ɛ', 'ɣ', 'ʏ', 'r']

    # These test cases can be handled by either LexiconGraphemeToPhonemeTranslator or SequiturGraphemeToPhonemeTranslator.
    # In this case, they should be handled by the former as ComposedTranslator was instantiated with it as first argument.
    def test_word_lexicon_01(self):
        text = "stormur"
        assert self._t.translate(text, self._language_code) == ['s', 't', 'ɔ', 'r', 'm', 'ʏ', 'r']

    def test_word_lexicon_02(self):
        text = "varnarmálaráðherra"
        assert self._t.translate(text, self._language_code) \
            == ['v', 'a', 'r', 't', 'n', 'a',
                'r', 'm', 'au', 'l', 'a', 'r',
                'au', 'θ', 'h', 'ɛ', 'r', 'a']

    # Neither of the Translators in ComposedTranslator should be able to process these strings.
    def test_foreign_char_01(self):
        text = "Султан"
        assert self._t.translate(text, self._language_code) == []

    def test_foreign_char_02(self):
        text = "дlvдrlegt"
        assert self._t.translate(text, self._language_code) == []            

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

    def test_empty(self):
        text: str = ""
        assert self._t.translate(text, self._language_code) == []

    def test_multiword(self):
        text: str = "Halló heimur"
        assert self._t.translate(text, self._language_code) == ['h', 'a', 't', 'l', 'ou', 'h', 'eiː', 'm', 'ʏ', 'r']

    def test_incorrect_data_type(self):
        text: int = 15
        with raises(AttributeError):
            self._t.translate(text, self._language_code)

    def test_word_lower_01(self):
        text = "stormur"
        assert self._t.translate(text, self._language_code) == ['s', 't', 'ɔ', 'r', 'm', 'ʏ', 'r']

    def test_word_lower_02(self):
        text = "varnarmálaráðherra"
        assert self._t.translate(text, self._language_code) \
            == ['v', 'a', 'r', 't', 'n', 'a',
                'r', 'm', 'au', 'l', 'a', 'r',
                'au', 'θ', 'h', 'ɛ', 'r', 'a']

    def test_word_nonexistant_01(self):
        text = "kleprar"
        assert self._t.translate(text, self._language_code) == []

    def test_word_nonexistant_02(self):
        text = "blöðrupumpur"
        assert self._t.translate(text, self._language_code) == []

    def test_foreign_char_01(self):
        text = "Султан"
        assert self._t.translate(text, self._language_code) == []

    def test_foreign_char_02(self):
        text = "дlvдrlegt"
        assert self._t.translate(text, self._language_code) == []

    def test_sentence(self):
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

    def test_sentence_punctuated(self):
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

    def test_empty(self):
        text: str = ""
        assert self._t.translate(text, self._language_code) == []

    def test_multiword(self):
        text: str = "Halló heimur"
        assert self._t.translate(text, self._language_code) == ['h', 'a', 'l', 'ou', 'h', 'eiː', 'm', 'ʏ', 'r']

    def test_incorrect_data_type(self):
        text: int = 15
        with raises(AttributeError):
            self._t.translate(text, self._language_code)

    def test_word_lower_01(self):
        text = "kleprar"
        assert self._t.translate(text, self._language_code) == ['kʰ', 'l', 'ɛː', 'p', 'r', 'a', 'r']

    def test_word_lower_02(self):
        text = "blöðrupumpur"
        assert self._t.translate(text, self._language_code) == ['p', 'l', 'œ', 'ð', 'r', 'ʏ', 'pʰ', 'ʏ', 'm̥', 'p', 'ʏ', 'r']

    def test_word_capital_first(self):
        text = "Blöðrupumpur"
        assert self._t.translate(text, self._language_code) == ['p', 'l', 'œ', 'ð', 'r', 'ʏ', 'pʰ', 'ʏ', 'm̥', 'p', 'ʏ', 'r']

    def test_word_all_caps(self):
        text = "FJANDSAMLEGUR"
        assert self._t.translate(text, self._language_code) == ['f', 'j', 'a', 'n', 't', 's', 'a', 'm', 'l', 'ɛ', 'ɣ', 'ʏ', 'r']

    def test_foreign_char_01(self):
        text = "Султан"
        assert self._t.translate(text, self._language_code) == []

    def test_foreign_char_02(self):
        text = "дlvдrlegt"
        assert self._t.translate(text, self._language_code) == []

    def test_sentence(self):
        text = "ekki voru allir á sama máli um hvað ætti að gera við Vigfús"
        assert self._t.translate(text, self._language_code)  \
            == ['ɛ', 'h', 'c', 'ɪ', 'v', 'ɔː',
                'r', 'ʏ', 'a', 't', 'l', 'ɪ',
                'r', 'auː', 's', 'aː', 'm', 'a',
                'm', 'auː', 'l', 'ɪ', 'ʏ', 'm',
                'kʰ', 'v', 'aː', 'ð', 'ai', 'h',
                't', 'ɪ', 'aː', 'ð', 'c', 'ɛː',
                'r', 'a', 'v', 'ɪː', 'ð', 'v',
                'ɪ', 'x', 'f', 'u', 's']

    def test_sentence_punctuated(self):
        text = "Flestum þótti Vigfús vera ómerkilegur, enda með eindæmum venjulegur í framkomu."
        assert self._t.translate(text, self._language_code)  \
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
                'r', 'a', 'm', 'k', 'ɔ', 'm',
                'ʏ', 'sp']