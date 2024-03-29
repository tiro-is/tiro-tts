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
import re
import string
import unicodedata
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Literal, Optional, Tuple, cast

import grpc
import tokenizer
from messages import tts_frontend_message_pb2
from services import tts_frontend_service_pb2, tts_frontend_service_pb2_grpc
from tokenizer import Tok

from src.frontend.common import (
    SSMLConsumer,
    consume_whitespace,
    is_partially_numeric,
    utf8_byte_length,
)
from src.frontend.ssml import OldSSMLParser as SSMLParser
from src.frontend.words import (
    WORD_SENTENCE_SEPARATOR,
    PhonemeProps,
    ProsodyProps,
    SSMLProps,
    Word,
)
from src.utils.version import VersionedThing, hash_from_impl


class NormalizerBase(VersionedThing, ABC):
    @abstractmethod
    def normalize(self, text: str, ssml_reqs: Dict) -> Iterable[Word]:
        ...

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

        # TODO(Smári): See if I can move these two variables to SSMLConsumer:_tag_metadata.
        acc_consumption_status: List[Dict] = []
        acc_normalized: List[str] = []
        for sent in sentences_with_pairs:
            last_ssml_props: Optional[SSMLProps] = None
            for original, normalized in sent:
                consumption_status: Dict = consumer.consume(original)
                ssml_props: SSMLProps = consumption_status["ssml_props"]

                if (
                    (
                        isinstance(last_ssml_props, ProsodyProps)
                        and not isinstance(ssml_props, ProsodyProps)
                    )
                    or (
                        isinstance(last_ssml_props, ProsodyProps)
                        and isinstance(ssml_props, ProsodyProps)
                        and ssml_props != last_ssml_props
                    )
                    or (
                        not isinstance(last_ssml_props, ProsodyProps)
                        and isinstance(ssml_props, ProsodyProps)
                    )
                ):
                    # TODO(rkjaran): This will fail if the current <prosody>
                    #   includes nested tags. Fix once we can accumulate SSML
                    #   properties
                    yield WORD_SENTENCE_SEPARATOR

                if ssml_props.tag_type in ("speak", "prosody"):
                    yield Word(
                        original_symbol=original,
                        symbol=normalized,
                        start_byte_offset=consumption_status["start_byte_offset"],
                        end_byte_offset=consumption_status["end_byte_offset"],
                        ssml_props=ssml_props,
                    )
                elif ssml_props.tag_type == "phoneme":
                    if ssml_props.is_multi():
                        # If a phoneme tag contains more than a single word, we must accumulate
                        # all of them and yield them as a single Word.

                        acc_consumption_status.append(consumption_status)
                        if not consumption_status["last_word"]:
                            continue

                        yield Word(
                            original_symbol=ssml_props.get_data(),
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
                        acc_consumption_status.clear()
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
                elif ssml_props.tag_type == "sub":
                    sub_consumption: bool = consumption_status["tag_metadata"][
                        "needs_sub_consumption"
                    ]

                    if sub_consumption:
                        # If a sub tag's alias attribute contains more than a single word, we only need the consumption status
                        # from the first consumption_status, it contains all the data necessary. For the rest of them, we only
                        # need to accumulate the normalized words before joining them and assigning them to Word:symbol before
                        # yielding.

                        acc_normalized.append(normalized)
                        if not consumption_status["tag_metadata"]["alias_last_word"]:
                            continue

                    yield Word(
                        original_symbol=ssml_props.get_data().strip(),
                        symbol=" ".join(acc_normalized)
                        if sub_consumption
                        else normalized,
                        start_byte_offset=consumption_status["start_byte_offset"],
                        end_byte_offset=consumption_status["end_byte_offset"],
                        ssml_props=ssml_props,
                    )
                    acc_normalized.clear()
                elif ssml_props.tag_type == "say-as":
                    if ssml_props.get_interpret_as() == "digits":
                        # Nonnumeric tokens within say-as->digits are yielded without any special treatment.                                    (symbol=normalized)
                        # Partially (or fully) numeric tokens, however, are interpreted and yielded as individual digits and characters.        (symbol=ssml_props.get_interpretation(original))

                        # Note: A multitoken say-as->digits tag does not yield a multitoken Word instance as is done for say-as->characters for example.
                        #       Example: "<say-as interpret-as="digits">förum kl. 18</say-as>" yields
                        #           [
                        #               Word({ original: "förum", normalized: "förum" }),
                        #               Word({ original: "kl.", normalized: "klukkan" }),
                        #               Word({ original: "18", normalized: "einn, átta" }),
                        #           ]
                        #
                        #       Example: "<say-as interpret-as="digits">18b</say-as>" yields
                        #           [
                        #               Word({ original: "18b", normalized: "einn, átta, b" })
                        #           ]
                        #
                        #       Example: "<say-as interpret-as="digits">112</say-as>" yields
                        #           [
                        #               Word({ original: "112", normalized: "einn, einn, tveir" })
                        #           ]
                        yield Word(
                            original_symbol=original,
                            symbol=ssml_props.get_interpretation(original)
                            if is_partially_numeric(original)
                            else normalized,
                            start_byte_offset=consumption_status["start_byte_offset"],
                            end_byte_offset=consumption_status["end_byte_offset"],
                            ssml_props=ssml_props,
                        )
                    elif (
                        ssml_props.is_multi()
                        or consumption_status["tag_metadata"]["kennitala_multi_token"]
                    ):
                        # If a say-as tag contains more than a single word, we must accumulate
                        # all of them and yield them as a single Word.

                        acc_consumption_status.append(consumption_status)
                        if not consumption_status["last_word"]:
                            continue

                        yield Word(
                            original_symbol=ssml_props.get_data().strip(),
                            symbol=ssml_props.get_interpretation(),
                            start_byte_offset=acc_consumption_status[0][
                                "start_byte_offset"
                            ],
                            end_byte_offset=acc_consumption_status[-1][
                                "end_byte_offset"
                            ],
                            ssml_props=ssml_props,
                        )
                        acc_consumption_status.clear()
                    else:
                        yield Word(
                            original_symbol=original,
                            symbol=ssml_props.get_interpretation(),
                            start_byte_offset=consumption_status["start_byte_offset"],
                            end_byte_offset=consumption_status["end_byte_offset"],
                            ssml_props=ssml_props,
                        )
                last_ssml_props = ssml_props
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
    _version_hash: Optional[str] = None

    @property
    def version_hash(self) -> str:
        if not self._version_hash:
            self._version_hash = hash_from_impl(self.__class__)
        return self._version_hash

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
    _address: str
    _version_hash: Optional[str] = None

    def __init__(self, address: str):
        self._address = address
        parsed_url = urllib.parse.urlparse(address)
        if parsed_url.scheme == "grpc":
            self._channel = grpc.insecure_channel(parsed_url.netloc)
        else:
            raise ValueError("Unsupported scheme in address '%s'", address)
        self._stub = tts_frontend_service_pb2_grpc.TTSFrontendStub(self._channel)

    @property
    def version_hash(self) -> str:
        if not self._version_hash:
            # Not really correct, but we don't have a way of getting any version info
            # from the server
            self._version_hash = hash_from_impl(self.__class__, self._address)
        return self._version_hash

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
