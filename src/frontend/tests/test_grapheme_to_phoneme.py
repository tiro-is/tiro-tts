import pytest

from src.frontend.grapheme_to_phoneme import IceG2PTranslator
from src.frontend.words import LangID, Word


@pytest.fixture()
def words():
    return [
        Word(original_symbol="kleprar", symbol="kleprar"),
        Word(original_symbol="eru", symbol="eru"),
        Word(original_symbol="kleprar", symbol="{kʰlɛːprar}"),
    ]


class TestIceG2PTranslator:
    _translator = IceG2PTranslator()
    _lang = LangID("is-IS")
    _syll_marker = Word(phone_sequence=["."])

    def test_ipa_target(self):
        output = self._translator.translate("kleprar", self._lang, alphabet="ipa")
        assert output == ["kʰ", "l", "ɛː", "p", "r", "a", "r"]

    def test_ipa_target_embedded_phonemes(self, words):
        output = list(
            self._translator.translate_words(words, self._lang, alphabet="ipa")
        )

        expected_output = [
            Word(
                original_symbol="kleprar",
                symbol="kleprar",
                phone_sequence=["kʰ", "l", "ɛː", "p", "r", "a", "r"],
            ),
            Word(
                original_symbol="eru",
                symbol="eru",
                phone_sequence=["ɛː", "r", "ʏ"],
            ),
            Word(
                original_symbol="kleprar",
                symbol="{kʰlɛːprar}",
                phone_sequence=["kʰ", "l", "ɛː", "p", "r", "a", "r"],
            ),
        ]

        assert output == expected_output

    def test_x_sampa_target(self):
        output = self._translator.translate("kleprar", self._lang, alphabet="x-sampa")
        assert output == ["k_h", "l", "E:", "p", "r", "a", "r"]

    def test_x_sampa_target_embedded_phonemes(self, words):
        output = list(
            self._translator.translate_words(words, self._lang, alphabet="x-sampa")
        )
        expected_output = [
            Word(
                original_symbol="kleprar",
                symbol="kleprar",
                phone_sequence=["k_h", "l", "E:", "p", "r", "a", "r"],
            ),
            Word(
                original_symbol="eru",
                symbol="eru",
                phone_sequence=["E:", "r", "Y"],
            ),
            Word(
                original_symbol="kleprar",
                symbol="{kʰlɛːprar}",
                phone_sequence=["k_h", "l", "E:", "p", "r", "a", "r"],
            ),
        ]

        assert output == expected_output

    def test_x_sampa_syll_and_stress_target(self):
        output = self._translator.translate(
            "kleprar", self._lang, alphabet="x-sampa+syll+stress"
        )
        assert output == ["k_h", "l", "E:1", ".", "p", "r", "a0", "r"]

    def test_x_sampa_syll_and_stress_target_embedded_phonemes(self, words):
        output = list(
            self._translator.translate_words(
                words, self._lang, alphabet="x-sampa+syll+stress"
            )
        )

        expected_output = [
            Word(
                original_symbol="kleprar",
                symbol="kleprar",
                phone_sequence=["k_h", "l", "E:1", ".", "p", "r", "a0", "r"],
            ),
            self._syll_marker,
            Word(
                original_symbol="eru",
                symbol="eru",
                phone_sequence=["E:1", ".", "r", "Y0"],
            ),
            self._syll_marker,
            Word(
                original_symbol="kleprar",
                symbol="{kʰlɛːprar}",
                phone_sequence=["k_h", "l", "E:1", ".", "p", "r", "a0", "r"],
            ),
            self._syll_marker,
        ]

        assert output == expected_output

    def test_version_hash(self):
        # The version hash is something that looks like a sha1 hash
        assert isinstance(self._translator.version_hash, str)
        assert len(self._translator.version_hash) == 40
