from pytest import raises

from ..phonemes import (
    SHORT_PAUSE,
    _align_ipa,
    align_ipa_from_xsampa,
    convert_ipa_to_xsampa,
    convert_xsampa_to_ipa,
)


class TestConvertIpaToXsampa:
    def test_empty_lis(self):
        assert convert_ipa_to_xsampa([]) == []

    def test_incorrect_strings_01(self):
        with raises(KeyError):
            convert_ipa_to_xsampa(["."])

    def test_incorrect_strings_02(self):
        with raises(KeyError):
            convert_ipa_to_xsampa(["a", "b", "c"])

    def test_incorrect_data_type_01(self):
        with raises(KeyError):
            convert_ipa_to_xsampa({"key": "val"})

    def test_incorrect_data_type_02(self):
        with raises(TypeError):
            convert_ipa_to_xsampa([{"key": "val"}])

    def test_a(self):
        assert convert_ipa_to_xsampa(["a"]) == ["a"]

    def test_p_h(self):
        assert convert_ipa_to_xsampa(["pʰ"]) == ["p_h"]

    def test_9i(self):
        assert convert_ipa_to_xsampa(["œy"]) == ["9i"]

    def test_T(self):
        assert convert_ipa_to_xsampa(["θ"]) == ["T"]

    def test_short_pause(self):
        assert convert_ipa_to_xsampa([SHORT_PAUSE]) == [SHORT_PAUSE]

    def test_toad(self):
        assert convert_ipa_to_xsampa(["t", "ɔː", "aː", "ð"]) == ["t", "O:", "a:", "D"]

    def test_fox(self):
        assert convert_ipa_to_xsampa(["f", "ɔ", "x"]) == ["f", "O", "x"]


class TestConvertXsampaToIpa:
    def test_empty_lis(self):
        assert convert_xsampa_to_ipa([]) == []

    def test_incorrect_strings_01(self):
        with raises(KeyError):
            convert_xsampa_to_ipa(["."])

    def test_incorrect_strings_02(self):
        with raises(KeyError):
            convert_xsampa_to_ipa(["a", "b", "c"])

    def test_incorrect_data_type_01(self):
        with raises(KeyError):
            convert_xsampa_to_ipa({"key": "val"})

    def test_incorrect_data_type_02(self):
        with raises(TypeError):
            convert_xsampa_to_ipa([{"key": "val"}])

    def test_a(self):
        assert convert_xsampa_to_ipa(["a"]) == ["a"]

    def test_p_h(self):
        assert convert_xsampa_to_ipa(["p_h"]) == ["pʰ"]

    def test_9i(self):
        assert convert_xsampa_to_ipa(["9i"]) == ["œy"]

    def test_T(self):
        assert convert_xsampa_to_ipa(["T"]) == ["θ"]

    def test_short_pause(self):
        assert convert_xsampa_to_ipa([SHORT_PAUSE]) == [SHORT_PAUSE]

    def test_toad(self):
        assert convert_xsampa_to_ipa(["t", "O:", "a:", "D"]) == ["t", "ɔː", "aː", "ð"]

    def test_fox(self):
        assert convert_xsampa_to_ipa(["f", "O", "x"]) == ["f", "ɔ", "x"]


class TestAlignIpaFromXsampa:
    def test_toad_no_space(self):
        assert align_ipa_from_xsampa("tO:a:D") == "t ɔː aː ð"

    def test_toad_spaces_and_tabs(self):
        assert align_ipa_from_xsampa("t     O:          a:  D") == "t ɔː aː ð"

    def test_single_spaces(self):
        assert align_ipa_from_xsampa("t O: a: D") == "t ɔː aː ð"

    def test_toad_invalid_symbol(self):
        with raises(ValueError):
            align_ipa_from_xsampa("t     O:          a:\t D")

    def test_empty_string(self):
        with raises(KeyError):
            align_ipa_from_xsampa("")

    def test_incorrect_data_type(self):
        with raises(AttributeError):
            align_ipa_from_xsampa(("a", 1))

    def test_single_symbol(self):
        assert align_ipa_from_xsampa("n_0") == "n̥"

    def test_toad_ipa(self):
        with raises(ValueError):
            align_ipa_from_xsampa("t ɔː aː ð")


class TestAlignIpa:
    def test_toad_no_space(self):
        assert _align_ipa("tɔːaːð") == "t ɔː aː ð"

    def test_toad_spaces_and_tabs(self):
        assert _align_ipa("t     ɔː          aː  ð") == "t ɔː aː ð"

    def test_single_spaces(self):
        assert _align_ipa("t ɔː aː ð") == "t ɔː aː ð"

    def test_toad_invalid_symbol(self):
        with raises(ValueError):
            _align_ipa("t     ɔː          aː\t  ð")

    def test_empty_string(self):
        print(_align_ipa("")) == ""

    def test_incorrect_data_type(self):
        with raises(AttributeError):
            _align_ipa(("a", 1))

    def test_single_symbol(self):
        assert _align_ipa("n̥") == "n̥"

    def test_toad_xsampa(self):
        with raises(ValueError):
            _align_ipa("tO:a:D")
