from typing import List, Tuple
from ..normalization import add_token_offsets,  \
                            BasicNormalizer

import tokenizer

class TestAddTokenOffsets:
    def _isolate_offset_data(self, tokens_with_offsets: List[Tuple[tokenizer.Tok, int, int]]) -> List[Tuple[int, int]]:
        """We are only testing the offset values that add_token_offsets adds and thus we omit the Tok instances from the tuples."""

        return list(map(lambda x: (x[1], x[2]), tokens_with_offsets))

    def test_empty(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation(""))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == []

    def test_char(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("b"))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 1), (0, 0)]

    def test_char_foreign(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("д"))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 2), (0, 0)]

    def test_word_01(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("appelsínusafi"))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 14), (0, 0)]

    def test_word_02(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("köngull"))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 8), (0, 0)]

    def test_short_sentence_01(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("Mennirnir notuðu áttavita."))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 9), (10, 17), (18, 27), (27, 28), (0, 0)]

    def test_short_sentence_02(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("Hann hafði hlotið mörg verðlaun."))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 4), (5, 11), (12, 19), (20, 25), (26, 35), (35, 36), (0, 0)]

    def test_sentence_01(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("Álfarnir lentu í ógöngum þegar þeir fóru í gegnum skóginn, enda óvanir háum trjám og mannætuköngulóm."))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [
            (0, 9), (10, 15), (16, 18), (19, 28), (29, 35),
            (36, 41), (42, 47), (48, 50), (51, 57), (58, 66),
            (66, 67), (68, 72), (73, 80), (81, 86), (87, 93), 
            (94, 96), (97, 115), (115, 116), (0, 0)
        ]

    def test_sentence_02(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("Stjórnmálamönnunum þótti það ekki tiltökumál að samþykkja þingsályktunartillöguna, jafnvel þótt hún var talin illa ígrunduð af minnihlutanum."))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [
            (0, 21), (22, 29), (30, 35), (36, 40), (41, 53), 
            (54, 57), (58, 68), (69, 95), (95, 96), (97, 104), 
            (105, 111), (112, 116), (117, 120), (121, 126), (127, 131), 
            (132, 142), (143, 145), (146, 159), (159, 160), (0, 0)
        ]

    def test_sentence_foreign_char(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("Það þótti ekki nógu kдrlmannlegt."))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(add_token_offsets(tokens))
        assert offsets == [(0, 5), (6, 13), (14, 18), (19, 24), (25, 38), (38, 39), (0, 0)]