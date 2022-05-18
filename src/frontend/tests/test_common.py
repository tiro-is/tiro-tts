from pytest import raises

from ..common import consume_whitespace, utf8_byte_length


class TestUtf8ByteLength:
    def test_empty_string(self):
        assert utf8_byte_length("") == 0

    def test_four_spaces(self):
        assert utf8_byte_length("    ") == 4

    def test_tab(self):
        assert utf8_byte_length("\t") == 1

    def test_string01(self):
        assert utf8_byte_length("Peter") == 5

    def test_string02(self):
        assert utf8_byte_length("peter") == 5

    def test_string03(self):
        assert utf8_byte_length("Örlygur") == 8

    def test_string04(self):
        assert utf8_byte_length("örlygur") == 8

    def test_sentence(self):
        assert utf8_byte_length("ragnar fór á fund") == 19

    def test_integer_string01(self):
        assert utf8_byte_length("100") == 3

    def test_integer_string02(self):
        assert utf8_byte_length("1001") == 4

    def test_incorrect_arg_int(self):
        with raises(AttributeError):
            utf8_byte_length(1337)

    def test_incorrect_arg_dict(self):
        with raises(AttributeError):
            utf8_byte_length({"meaning": 42})

    def test_no_arg(self):
        with raises(TypeError):
            utf8_byte_length()

    def test_extra_arg(self):
        with raises(TypeError):
            utf8_byte_length(" Marcus", "\tTullius")


class TestConsumeWhitespace:
    def test_empty_string(self):
        assert consume_whitespace("") == (0, 0)

    def test_four_spaces(self):
        assert consume_whitespace("    ") == (4, 4)

    def test_space(self):
        assert consume_whitespace(" ") == (1, 1)

    def test_tab_prefix(self):
        assert consume_whitespace(" ragnar fór á fund") == (1, 1)

    def test_two_tab_prefix(self):
        assert consume_whitespace("\t\tragnar fór á fund") == (2, 2)

    def test_four_spaces_prefix(self):
        assert consume_whitespace("    afi minn fór á honum rauð") == (4, 4)

    def test_tab_three_spaces_prefix(self):
        assert consume_whitespace("\t   örlygur") == (4, 4)

    def test_space_tab(self):
        assert consume_whitespace(" \tragnar fór á fund   ") == (2, 2)

    def test_space_postfix(self):
        assert consume_whitespace("100 ") == (0, 0)

    def test_tab_space_tab_postfix(self):
        assert consume_whitespace("1001\t  \t") == (0, 0)

    def test_incorrect_arg_int(self):
        with raises(TypeError):
            consume_whitespace(1337)

    def test_incorrect_arg_dict(self):
        with raises(TypeError):
            consume_whitespace({"meaning": 42})

    def test_no_arg(self):
        with raises(TypeError):
            consume_whitespace()

    def test_extra_arg(self):
        with raises(TypeError):
            consume_whitespace(" Marcus", "\tTullius")
