from pytest import raises

from ..common import utf8_byte_length, consume_whitespace, consume_whitespace_bytes

class TestUtf8ByteLength:
    def test_one_empty_string(self):
        assert utf8_byte_length("") == 0

    def test_two_four_spaces(self):
        assert utf8_byte_length("    ") == 4

    def test_three_tab(self):
        assert utf8_byte_length("\t") == 1

    def test_four_string01(self):
        assert utf8_byte_length("Peter") == 5

    def test_five_string02(self):
        assert utf8_byte_length("peter") == 5

    def test_six_string03(self):
        assert utf8_byte_length("Örlygur") == 8

    def test_seven_string04(self):
        assert utf8_byte_length("örlygur") == 8

    def test_eight_sentence(self):
        assert utf8_byte_length("ragnar fór á fund") == 19

    def test_nine_integer_string01(self):
        assert utf8_byte_length("100") == 3

    def test_ten_integer_string02(self):
        assert utf8_byte_length("1001") == 4

    def test_eleven_incorrect_arg_int(self):
        with raises(AttributeError):
            utf8_byte_length(1337)

    def test_twelve_incorrect_arg_dict(self):
        with raises(AttributeError):
            utf8_byte_length({'meaning': 42})

    def test_thirteen_no_arg(self):
        with raises(TypeError):
            utf8_byte_length()

    def test_fourteen_extra_arg(self):
        with raises(TypeError):
            utf8_byte_length(" Marcus", "\tTullius")
    
class TestConsumeWhitespace():
    def test_one_empty_string(self):
        assert consume_whitespace("") == (0,0)

    def test_two_four_spaces(self):
        assert consume_whitespace("    ") == (4,4)
    
    def test_three_space(self):
        assert consume_whitespace(" ") == (1,1)

    def test_four_tab_prefix(self):
        assert consume_whitespace(" ragnar fór á fund") == (1,1)

    def test_five_two_tab_prefix(self):
        assert consume_whitespace("\t\tragnar fór á fund") == (2,2)

    def test_six_four_spaces_prefix(self):
        assert consume_whitespace("    afi minn fór á honum rauð") == (4,4)

    def test_seven_tab_three_spaces_prefix(self):
        assert consume_whitespace("\t   örlygur") == (4,4)

    def test_eight_space_tab(self):
        assert consume_whitespace(" \tragnar fór á fund   ") == (2,2)

    def test_nine_space_postfix(self):
        assert consume_whitespace("100 ") == (0,0)

    def test_ten_tab_space_tab_postfix(self):
        assert consume_whitespace("1001\t  \t") == (0,0)

    def test_eleven_incorrect_arg_int(self):
        with raises(TypeError):
            consume_whitespace(1337)

    def test_twelve_incorrect_arg_dict(self):
        with raises(TypeError):
            consume_whitespace({'meaning': 42})

    def test_thirteen_no_arg(self):
        with raises(TypeError):
            consume_whitespace()

    def test_fourteen_extra_arg(self):
        with raises(TypeError):
            consume_whitespace(" Marcus", "\tTullius")

class TestConsumeWhitespaceBytes:
    def test_one_empty(self):
        assert consume_whitespace_bytes(b"") == 0

    def test_two_four_spaces(self):
        assert consume_whitespace_bytes(b"    ") == 4

    def test_three_space(self):
        assert consume_whitespace_bytes(b" ") == 1

    def test_four_tab_prefix(self):
        assert consume_whitespace_bytes(b" fiskurinn veiddist vel") == 1

    def test_five_two_tab_prefix(self):
        assert consume_whitespace_bytes(b"\t\tstrekkingsvindur") == 2

    def test_six_four_spaces_prefix(self):
        assert consume_whitespace_bytes(b"    baldvin reyndist vera svikari") == 4

    def test_seven_tab_three_spaces_prefix(self):
        assert consume_whitespace_bytes(b"\t   harkalegt") == 4

    def test_eight_space_tab(self):
        assert consume_whitespace_bytes(b" \tkastalakosningar     ") == 2

    def test_nine_space_postfix(self):
        assert consume_whitespace_bytes(b"100 ") == 0

    def test_ten_tab_space_tab_postfix(self):
        assert consume_whitespace_bytes(b"1001\t \t") == 0

    def test_eleven_arg_int(self):
        with raises(TypeError):
            consume_whitespace_bytes(1337)

    def test_twelve_incorrect_arg_str(self):
        with raises(TypeError):
            consume_whitespace_bytes("Þessi strengur er ekki í bætum")

    def test_thirteen_no_arg(self):
        with raises(TypeError):
            consume_whitespace_bytes()

    def test_fourteen_extra_arg(self):
        with raises(TypeError):
            consume_whitespace_bytes(b"asdf", b"qwerty")