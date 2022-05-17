from typing import Iterable, List, Tuple

import tokenizer

from ..normalization import _tokenize, add_token_offsets


class TestAddTokenOffsets:
    def _isolate_offset_data(
        self, tokens_with_offsets: List[Tuple[tokenizer.Tok, int, int]]
    ) -> List[Tuple[int, int]]:
        """We are only testing the offset values that add_token_offsets adds and thus we omit the Tok instances from the tuples."""

        return list(map(lambda x: (x[1], x[2]), tokens_with_offsets))

    def test_empty(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation(""))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == []

    def test_char(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("b"))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [(0, 1), (0, 0)]

    def test_char_foreign(self):
        tokens: list[tokenizer.Tok] = list(tokenizer.tokenize_without_annotation("д"))
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [(0, 2), (0, 0)]

    def test_word_01(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation("appelsínusafi")
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [(0, 14), (0, 0)]

    def test_word_02(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation("köngull")
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [(0, 8), (0, 0)]

    def test_short_sentence_01(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation("Mennirnir notuðu áttavita.")
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [(0, 9), (10, 17), (18, 27), (27, 28), (0, 0)]

    def test_short_sentence_02(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation("Hann hafði hlotið mörg verðlaun.")
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [
            (0, 4),
            (5, 11),
            (12, 19),
            (20, 25),
            (26, 35),
            (35, 36),
            (0, 0),
        ]

    def test_sentence_01(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation(
                "Álfarnir lentu í ógöngum þegar þeir fóru í gegnum skóginn, enda óvanir háum trjám og mannætuköngulóm."
            )
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [
            (0, 9),
            (10, 15),
            (16, 18),
            (19, 28),
            (29, 35),
            (36, 41),
            (42, 47),
            (48, 50),
            (51, 57),
            (58, 66),
            (66, 67),
            (68, 72),
            (73, 80),
            (81, 86),
            (87, 93),
            (94, 96),
            (97, 115),
            (115, 116),
            (0, 0),
        ]

    def test_sentence_02(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation(
                "Stjórnmálamönnunum þótti það ekki tiltökumál að samþykkja þingsályktunartillöguna, jafnvel þótt hún var talin illa ígrunduð af minnihlutanum."
            )
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [
            (0, 21),
            (22, 29),
            (30, 35),
            (36, 40),
            (41, 53),
            (54, 57),
            (58, 68),
            (69, 95),
            (95, 96),
            (97, 104),
            (105, 111),
            (112, 116),
            (117, 120),
            (121, 126),
            (127, 131),
            (132, 142),
            (143, 145),
            (146, 159),
            (159, 160),
            (0, 0),
        ]

    def test_sentence_foreign_char(self):
        tokens: list[tokenizer.Tok] = list(
            tokenizer.tokenize_without_annotation("Það þótti ekki nógu kдrlmannlegt.")
        )
        offsets: List[Tuple[int, int]] = self._isolate_offset_data(
            add_token_offsets(tokens)
        )
        assert offsets == [
            (0, 5),
            (6, 13),
            (14, 18),
            (19, 24),
            (25, 38),
            (38, 39),
            (0, 0),
        ]


class TestTokenize:
    # NOTE: Word does not have the equals (==) operator implemented. Therefore, we test equality
    # by serializing the objects to JSON and compare the string values.

    def test_empty(self):
        tokenized_text: Iterable[str] = [word.to_json() for word in _tokenize("")]
        assert tokenized_text == []

    def test_char(self):
        tokenized_text: str = [word.to_json() for word in _tokenize("b")][0]
        assert (
            tokenized_text
            == '{"time": 0, "type": "word", "start": 0, "end": 1, "value": "b"}'
        )

    def test_char_foreign(self):
        tokenized_text: str = [word.to_json() for word in _tokenize("д")][0]
        assert (
            tokenized_text
            == '{"time": 0, "type": "word", "start": 0, "end": 2, "value": "д"}'
        )

    def test_word_01(self):
        tokenized_text: str = [word.to_json() for word in _tokenize("appelsínusafi")][0]
        assert (
            tokenized_text
            == '{"time": 0, "type": "word", "start": 0, "end": 14, "value": "appelsínusafi"}'
        )

    def test_word_02(self):
        tokenized_text: str = [word.to_json() for word in _tokenize("köngull")][0]
        assert (
            tokenized_text
            == '{"time": 0, "type": "word", "start": 0, "end": 8, "value": "köngull"}'
        )

    def test_short_sentence_01(self):
        tokenized_text: Iterable[str] = [
            word.to_json() for word in _tokenize("Mennirnir notuðu áttavita.")
        ]
        assert tokenized_text == [
            '{"time": 0, "type": "word", "start": 0, "end": 9, "value": "Mennirnir"}',
            '{"time": 0, "type": "word", "start": 10, "end": 17, "value": "notuðu"}',
            '{"time": 0, "type": "word", "start": 18, "end": 27, "value": "áttavita"}',
            '{"time": 0, "type": "word", "start": 27, "end": 28, "value": "."}',
            '{"time": 0, "type": "word", "start": 0, "end": 0, "value": ""}',
        ]

    def test_short_sentence_02(self):
        tokenized_text: Iterable[str] = [
            word.to_json() for word in _tokenize("Hann hafði hlotið mörg verðlaun.")
        ]
        assert tokenized_text == [
            '{"time": 0, "type": "word", "start": 0, "end": 4, "value": "Hann"}',
            '{"time": 0, "type": "word", "start": 5, "end": 11, "value": "hafði"}',
            '{"time": 0, "type": "word", "start": 12, "end": 19, "value": "hlotið"}',
            '{"time": 0, "type": "word", "start": 20, "end": 25, "value": "mörg"}',
            '{"time": 0, "type": "word", "start": 26, "end": 35, "value": "verðlaun"}',
            '{"time": 0, "type": "word", "start": 35, "end": 36, "value": "."}',
            '{"time": 0, "type": "word", "start": 0, "end": 0, "value": ""}',
        ]

    def test_sentence_01(self):
        tokenized_text: Iterable[str] = [
            word.to_json()
            for word in _tokenize(
                "Álfarnir lentu í ógöngum þegar þeir fóru í gegnum skóginn, enda óvanir háum trjám og mannætuköngulóm."
            )
        ]
        assert tokenized_text == [
            '{"time": 0, "type": "word", "start": 0, "end": 9, "value": "Álfarnir"}',
            '{"time": 0, "type": "word", "start": 10, "end": 15, "value": "lentu"}',
            '{"time": 0, "type": "word", "start": 16, "end": 18, "value": "í"}',
            '{"time": 0, "type": "word", "start": 19, "end": 28, "value": "ógöngum"}',
            '{"time": 0, "type": "word", "start": 29, "end": 35, "value": "þegar"}',
            '{"time": 0, "type": "word", "start": 36, "end": 41, "value": "þeir"}',
            '{"time": 0, "type": "word", "start": 42, "end": 47, "value": "fóru"}',
            '{"time": 0, "type": "word", "start": 48, "end": 50, "value": "í"}',
            '{"time": 0, "type": "word", "start": 51, "end": 57, "value": "gegnum"}',
            '{"time": 0, "type": "word", "start": 58, "end": 66, "value": "skóginn"}',
            '{"time": 0, "type": "word", "start": 66, "end": 67, "value": ","}',
            '{"time": 0, "type": "word", "start": 68, "end": 72, "value": "enda"}',
            '{"time": 0, "type": "word", "start": 73, "end": 80, "value": "óvanir"}',
            '{"time": 0, "type": "word", "start": 81, "end": 86, "value": "háum"}',
            '{"time": 0, "type": "word", "start": 87, "end": 93, "value": "trjám"}',
            '{"time": 0, "type": "word", "start": 94, "end": 96, "value": "og"}',
            '{"time": 0, "type": "word", "start": 97, "end": 115, "value": "mannætuköngulóm"}',
            '{"time": 0, "type": "word", "start": 115, "end": 116, "value": "."}',
            '{"time": 0, "type": "word", "start": 0, "end": 0, "value": ""}',
        ]

    def test_sentence_02(self):
        tokenized_text: Iterable[str] = [
            word.to_json()
            for word in _tokenize(
                "Stjórnmálamönnunum þótti það ekki tiltökumál að samþykkja þingsályktunartillöguna, jafnvel þótt hún var talin illa ígrunduð af minnihlutanum."
            )
        ]
        assert tokenized_text == [
            '{"time": 0, "type": "word", "start": 0, "end": 21, "value": "Stjórnmálamönnunum"}',
            '{"time": 0, "type": "word", "start": 22, "end": 29, "value": "þótti"}',
            '{"time": 0, "type": "word", "start": 30, "end": 35, "value": "það"}',
            '{"time": 0, "type": "word", "start": 36, "end": 40, "value": "ekki"}',
            '{"time": 0, "type": "word", "start": 41, "end": 53, "value": "tiltökumál"}',
            '{"time": 0, "type": "word", "start": 54, "end": 57, "value": "að"}',
            '{"time": 0, "type": "word", "start": 58, "end": 68, "value": "samþykkja"}',
            '{"time": 0, "type": "word", "start": 69, "end": 95, "value": "þingsályktunartillöguna"}',
            '{"time": 0, "type": "word", "start": 95, "end": 96, "value": ","}',
            '{"time": 0, "type": "word", "start": 97, "end": 104, "value": "jafnvel"}',
            '{"time": 0, "type": "word", "start": 105, "end": 111, "value": "þótt"}',
            '{"time": 0, "type": "word", "start": 112, "end": 116, "value": "hún"}',
            '{"time": 0, "type": "word", "start": 117, "end": 120, "value": "var"}',
            '{"time": 0, "type": "word", "start": 121, "end": 126, "value": "talin"}',
            '{"time": 0, "type": "word", "start": 127, "end": 131, "value": "illa"}',
            '{"time": 0, "type": "word", "start": 132, "end": 142, "value": "ígrunduð"}',
            '{"time": 0, "type": "word", "start": 143, "end": 145, "value": "af"}',
            '{"time": 0, "type": "word", "start": 146, "end": 159, "value": "minnihlutanum"}',
            '{"time": 0, "type": "word", "start": 159, "end": 160, "value": "."}',
            '{"time": 0, "type": "word", "start": 0, "end": 0, "value": ""}',
        ]

    def test_sentence_foreign_char(self):
        tokenized_text: Iterable[str] = [
            word.to_json() for word in _tokenize("Það þótti ekki nógu kдrlmannlegt.")
        ]
        assert tokenized_text == [
            '{"time": 0, "type": "word", "start": 0, "end": 5, "value": "Það"}',
            '{"time": 0, "type": "word", "start": 6, "end": 13, "value": "þótti"}',
            '{"time": 0, "type": "word", "start": 14, "end": 18, "value": "ekki"}',
            '{"time": 0, "type": "word", "start": 19, "end": 24, "value": "nógu"}',
            '{"time": 0, "type": "word", "start": 25, "end": 38, "value": "kдrlmannlegt"}',
            '{"time": 0, "type": "word", "start": 38, "end": 39, "value": "."}',
            '{"time": 0, "type": "word", "start": 0, "end": 0, "value": ""}',
        ]

    def test_num_char(self):
        tokenized_text: str = [word.to_json() for word in _tokenize("15")][0]
        assert (
            tokenized_text
            == '{"time": 0, "type": "word", "start": 0, "end": 2, "value": "15"}'
        )

    def test_sentence_num_char(self):
        tokenized_text: Iterable[str] = [
            word.to_json() for word in _tokenize("Klukkan var langt gengin í 7.")
        ]
        assert tokenized_text == [
            '{"time": 0, "type": "word", "start": 0, "end": 7, "value": "Klukkan"}',
            '{"time": 0, "type": "word", "start": 8, "end": 11, "value": "var"}',
            '{"time": 0, "type": "word", "start": 12, "end": 17, "value": "langt"}',
            '{"time": 0, "type": "word", "start": 18, "end": 24, "value": "gengin"}',
            '{"time": 0, "type": "word", "start": 25, "end": 27, "value": "í"}',
            '{"time": 0, "type": "word", "start": 28, "end": 29, "value": "7"}',
            '{"time": 0, "type": "word", "start": 29, "end": 30, "value": "."}',
            '{"time": 0, "type": "word", "start": 0, "end": 0, "value": ""}',
        ]
