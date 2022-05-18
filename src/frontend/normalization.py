# Copyright 2021-2022 Tiro ehf.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from itertools import islice
import re
import string
import unicodedata
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Literal, Tuple, cast

import grpc
import tokenizer
from messages import tts_frontend_message_pb2
from services import tts_frontend_service_pb2, tts_frontend_service_pb2_grpc
from tokenizer import Tok

from src.frontend.common import consume_whitespace, SSMLConsumer, utf8_byte_length
from src.frontend.ssml import OldSSMLParser as SSMLParser
from src.frontend.words import WORD_SENTENCE_SEPARATOR, SSMLProps, Word


class NormalizerBase(ABC):
    @abstractmethod
    def normalize(self, text: str, ssml_reqs: Dict) -> Iterable[Word]:
        return NotImplemented

    def _parse_ssml(self, ssml: str) -> str:
        """Sanitizes and isolates text from SSML"""
        parser = SSMLParser()
        parser.feed(ssml)
        text: str = parser.get_text()
        parser.close()
        return text

    def _normalize_ssml(
        self,
        ssml: str,
        sentences_with_pairs: List[List[Tuple[str, str]]],
        alphabet: Literal["ipa", "x-sampa", "x-sampa+syll+stress"],
    ):
        if alphabet not in ["ipa", "x-sampa", "x-sampa+syll+stress"]:
            raise ValueError("Illegal alphabet choice: {}".format(alphabet))

        consumer = SSMLConsumer(ssml=ssml)
        acc_consumption_status: List[Dict] = []
        for sent in sentences_with_pairs:
            for original, normalized in sent:
                consumption_status = consumer.consume(original)
                ssml_props: SSMLProps = consumption_status["ssml_props"]
                if ssml_props.tag_type == "speak":
                    yield Word(
                        original_symbol=original,
                        symbol=normalized,
                        start_byte_offset=consumption_status["start_byte_offset"],
                        end_byte_offset=consumption_status["end_byte_offset"],
                        ssml_props=ssml_props,
                    )
                elif ssml_props.tag_type == "phoneme":
                    if ssml_props.is_multi():
                        # If a phoneme tags contains more than a single word, we must accumulate
                        # all of them and yield them as a single Word.

                        acc_consumption_status.append(consumption_status)
                        if not ssml_props.data_last_word:
                            continue

                        yield Word(
                            original_symbol=ssml_props.data,
                            symbol=normalized,
                            start_byte_offset=acc_consumption_status[0][
                                "start_byte_offset"
                            ],
                            end_byte_offset=acc_consumption_status[-1][
                                "end_byte_offset"
                            ],
                            phone_sequence=ssml_props.get_phone_sequence(alphabet),
                            ssml_props=ssml_props,
                        )
                    else:
                        yield Word(
                            original_symbol=original,
                            # Will not be used during translation but is required for an edge case where
                            # a "." or "," token is contained within a phoneme tag.
                            symbol=normalized,
                            start_byte_offset=consumption_status["start_byte_offset"],
                            end_byte_offset=consumption_status["end_byte_offset"],
                            phone_sequence=ssml_props.get_phone_sequence(alphabet),
                            ssml_props=ssml_props,
                        )

            yield WORD_SENTENCE_SEPARATOR


def add_token_offsets(
    tokens: Iterable[tokenizer.Tok],
) -> List[Tuple[tokenizer.Tok, int, int]]:
    """Calculate byte offsets of each token

    Args:
      tokens: an Iterable of Tokenizer tokens

    Returns:
      A list of tuples (token, start_byte_offset, end_byte_offset)
    """
    # can't throw away sentence end/start info
    n_bytes_consumed: int = 0
    byte_offsets: List[Tuple[tokenizer.Tok, int, int]] = []
    for tok in tokens:
        if tok.kind == tokenizer.TOK.S_END:
            byte_offsets.append((tok, 0, 0))
            continue
        if not tok.origin_spans or not tok.original:
            continue
        # if is_token_spoken(tok):
        start_offset = n_bytes_consumed + utf8_byte_length(
            tok.original[: tok.origin_spans[0]]
        )
        end_offset = start_offset + utf8_byte_length(
            tok.original[tok.origin_spans[0] : tok.origin_spans[-1] + 1]
        )

        byte_offsets.append((tok, start_offset, end_offset))
        n_bytes_consumed += utf8_byte_length(tok.original)
    return byte_offsets


def _tokenize(text: str) -> Iterable[Word]:
    """Split input into tokens.

    Args:
      text: Input text to be tokenized.

    Yields:
      Word: word symbols, including their *byte* offsets in `text`.  A
        default initialized Word represents a sentence boundary.

    """
    tokens = list(tokenizer.tokenize_without_annotation(text))

    for tok, start_byte_offset, end_byte_offset in add_token_offsets(tokens):
        if tok.kind == tokenizer.TOK.S_END:
            yield WORD_SENTENCE_SEPARATOR
            continue

        w = cast(str, tok.original).strip()
        yield Word(
            original_symbol=w,
            symbol=w,
            start_byte_offset=start_byte_offset,
            end_byte_offset=end_byte_offset,
        )


class BasicNormalizer(NormalizerBase):
    def normalize(self, text: str, ssml_reqs: Dict = None):
        if ssml_reqs != None and ssml_reqs["process_as_ssml"]:
            ssml_str = text
            text = self._parse_ssml(ssml_str)

            tok_lis: List[Tok] = list(tokenizer.tokenize_without_annotation(text))
            sentences_with_pairs: List[List[Tuple[str, str]]] = []
            for tok in tok_lis:
                if tok.kind == tokenizer.TOK.S_BEGIN:
                    sentences_with_pairs.append([])
                    continue
                elif tok.kind == tokenizer.TOK.S_END:
                    continue

                token: str = tok.original.strip()
                sentences_with_pairs[-1].append((token, token))
            return self._normalize_ssml(
                ssml_str, sentences_with_pairs, ssml_reqs["alphabet"]
            )
        else:
            return _tokenize(text)


class GrammatekNormalizer(NormalizerBase):
    _stub: tts_frontend_service_pb2_grpc.TTSFrontendStub
    _channel: grpc.Channel

    def __init__(self, address: str):
        parsed_url = urllib.parse.urlparse(address)
        if parsed_url.scheme == "grpc":
            self._channel = grpc.insecure_channel(parsed_url.netloc)
        else:
            raise ValueError("Unsupported scheme in address '%s'", address)
        self._stub = tts_frontend_service_pb2_grpc.TTSFrontendStub(self._channel)

    def normalize(self, text: str, ssml_reqs: Dict):
        process_as_ssml: bool = False
        if ssml_reqs != None and ssml_reqs["process_as_ssml"]:
            process_as_ssml = True
            ssml_str = text
            text = self._parse_ssml(ssml_str)

        response: tts_frontend_message_pb2.TokenBasedNormalizedResponse = (
            self._stub.NormalizeTokenwise(
                tts_frontend_message_pb2.NormalizeRequest(content=text)
            )
        )
        # TODO(rkjaran): Here we assume that the normalization process does not change
        #   the order of tokens, so that the order of original_tokens and normalized
        #   tokens is the same.  Fix this once it doesn't hold true any more.
        sentences_with_pairs: List[List[Tuple[str, str]]] = []
        for sent in response.sentence:
            sentences_with_pairs.append(
                [
                    (token_info.original_token, token_info.normalized_token)
                    for token_info in sent.token_info
                ]
            )

        if process_as_ssml:
            return self._normalize_ssml(
                ssml_str, sentences_with_pairs, ssml_reqs["alphabet"]
            )
        else:
            return self._normalize_text(text, sentences_with_pairs)

    def _normalize_text(
        self, text: str, sentences_with_pairs: List[List[Tuple[str, str]]]
    ):
        n_bytes_consumed = 0
        text_view = text
        for sent in sentences_with_pairs:
            for original, normalized in sent:
                n_chars_whitespace, n_bytes_whitespace = consume_whitespace(text_view)
                n_bytes_consumed += n_bytes_whitespace
                token_byte_len = utf8_byte_length(original)

                yield Word(
                    original_symbol=original,
                    symbol=normalized,
                    start_byte_offset=n_bytes_consumed,
                    end_byte_offset=n_bytes_consumed + token_byte_len,
                )
                n_bytes_consumed += token_byte_len
                text_view = text_view[n_chars_whitespace + len(original) :]
            yield WORD_SENTENCE_SEPARATOR
