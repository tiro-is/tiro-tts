from ..common import utf8_byte_length, consume_whitespace, consume_whitespace_bytes

class TestUtf8ByteLength:
    def test_one(self):
        assert utf8_byte_length("") == 0

    def test_two(self):
        assert utf8_byte_length("    ") == 4

    def test_three(self):
        assert utf8_byte_length("\t") == 1

    def test_four(self):
        assert utf8_byte_length("Peter") == 5

    def test_five(self):
        assert utf8_byte_length("peter") == 5

    def test_six(self):
        assert utf8_byte_length("Örlygur") == 8

    def test_seven(self):
        assert utf8_byte_length("örlygur") == 8

    def test_eight(self):
        assert utf8_byte_length("ragnar fór á fund") == 19

    def test_nine(self):
        assert utf8_byte_length("100") == 3

    def test_ten(self):
        assert utf8_byte_length("1001") == 4
    
def test_consume_whitespace():
    assert True

def test_consume_whitespace_bytes():
    assert True