from ..words import Word

class TestWord:
    def test_is_spoken_empty_string(self):
        word: Word = Word(original_symbol="",
                    symbol="",
                    start_byte_offset=3,
                    end_byte_offset=3)

        assert not word.is_spoken()

    def test_is_spoken_symbol(self):
        word: Word = Word(original_symbol="»",
                    symbol="»",
                    start_byte_offset=3,
                    end_byte_offset=3)

        assert not word.is_spoken()

    def test_is_spoken_single_letter_word(self):
        word: Word = Word(original_symbol="á",
                    symbol="á",
                    start_byte_offset=3,
                    end_byte_offset=4)

        assert word.is_spoken()

    def test_is_spoken_word_01(self):
        word: Word = Word(original_symbol="3.",
                    symbol="þriðji",
                    start_byte_offset=5,
                    end_byte_offset=6)

        assert word.is_spoken()

    def test_is_spoken_word_02(self):
        word: Word = Word(original_symbol="t.d.",
                    symbol="til dæmis",
                    start_byte_offset=3,
                    end_byte_offset=6)

        assert word.is_spoken()