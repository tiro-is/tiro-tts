# Copyright 2022 Tiro ehf.
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
from typing import Any, Dict, List, Literal, Pattern, Tuple

from regex import Match

from src.frontend.words import (
    PhonemeProps,
    ProsodyProps,
    SayAsProps,
    SpeakProps,
    SSMLProps,
    SubProps,
)


def utf8_byte_length(text: str) -> int:
    return len(text.encode("utf-8"))


def consume_whitespace(text: str) -> Tuple[int, int]:
    """Consume whitespace prefix

    Returns:
      A tuple of the number of characters consumed and the number of bytes consumed.

    """
    WHITESPACE_REGEX = re.compile(r"^\s+", re.UNICODE)

    m = re.match(WHITESPACE_REGEX, text)
    if m:
        return len(m.group()), utf8_byte_length(m.group())
    return 0, 0


def is_partially_numeric(string: str) -> bool:
    for char in string:
        if char.isdecimal():
            return True
    return False


class SSMLConsumer:
    # General consumption variables
    _ssml: str
    _ssml_view: str
    _data: str

    _n_bytes_consumed: int

    _tag_stack: List[SSMLProps]

    TAG_REGEX: Pattern
    TAG_CLOSE_REGEX: Pattern
    SSML_WHITESPACE_REGEX: Pattern

    # Keys
    SPEAK: str = "speak"
    PHONEME: str = "phoneme"
    SUB: str = "sub"
    SAY_AS: str = "say-as"
    PROSODY: str = "prosody"

    _tag_metadata: Dict[str, Dict[str, Any]]

    def __init__(self, ssml) -> None:
        # General consumption variables
        self._ssml_view = ssml
        self._data = ""

        self._n_bytes_consumed = 0

        self._tag_stack = []

        TAG_PATTERN: str = r"<(\"[^\"]*\"|'[^']*'|[^'\">])*>"
        TAG_CLOSE_PATTERN: str = r"^\s*<\s*/\s*.*?\s*>"
        TAG_WHITESPACE_PATTERN: str = f"^\s*({TAG_PATTERN})?\s*"
        self.TAG_REGEX = re.compile(f"^\s*{TAG_PATTERN}", re.UNICODE)
        self.TAG_CLOSE_REGEX = re.compile(TAG_CLOSE_PATTERN, re.UNICODE)
        self.SSML_WHITESPACE_REGEX = re.compile(TAG_WHITESPACE_PATTERN, re.UNICODE)

        self._reset_tag_metadata()

    def _reset_tag_metadata(
        self, tag: Literal["all", "speak", "phoneme", "sub", "say-as"] = "all"
    ):
        if tag not in [
            "all",
            self.SPEAK,
            self.PHONEME,
            self.SUB,
            self.SAY_AS,
            self.PROSODY,
        ]:
            raise ValueError(f"Unsupported tag: {tag} - Unable to reset metadata.")

        INITIAL_STATE: Dict[str, Any] = {
            self.SPEAK: {},
            self.PHONEME: {},
            self.SUB: {
                "needs_sub_consumption": False,
                "alias_last_word": False,
                "alias_view": "",
            },
            self.SAY_AS: {},
            self.PROSODY: {},
        }

        if tag == "all":
            self._tag_metadata = {
                self.SPEAK: INITIAL_STATE[self.SPEAK],
                self.PHONEME: INITIAL_STATE[self.PHONEME],
                self.SUB: INITIAL_STATE[self.SUB],
                self.SAY_AS: INITIAL_STATE[self.SAY_AS],
                self.PROSODY: INITIAL_STATE[self.PROSODY],
            }
        else:
            self._tag_metadata[tag] = INITIAL_STATE[tag]

    def _update_ssml_view(self, len_consumption) -> None:
        self._ssml_view = self._ssml_view[len_consumption:]

    def _update_data(self) -> None:
        """Sets _data's value to all text within current tag"""
        data = re.findall(r">(.*?)<", self._ssml_view)
        self._data = data[0] if data else ""

    def _extract_tag_attrs(self, tag_val: str) -> Dict[str, str]:
        """Extracts tag attributes from tags."""

        # Note: This should already be sanitized by SSMLParser earlier in the process.
        err_msg: str = "{} tag did not supply the required attributes!\n{}"
        if self.PHONEME in tag_val:
            alphabet: List[Tuple] = re.findall(
                r"alphabet\s*=\s*(\"|'{1}(x-sampa|ipa)(\"|'){1})", tag_val
            )
            ph: List[Tuple] = re.findall(r"ph\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val)

            if len(alphabet) == 0 or len(ph) == 0:
                raise AttributeError(err_msg.format(self.PHONEME, tag_val))
            if len(alphabet[0]) < 2 or len(ph[0]) < 2:
                raise AttributeError(err_msg.format(self.PHONEME, tag_val))

            return {
                "alphabet": alphabet[0][1],
                "ph": ph[0][1],
            }
        elif self.SUB in tag_val:
            alias: List[Tuple] = re.findall(
                r"alias\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val
            )
            if len(alias) == 0:
                raise AttributeError(err_msg.format(self.SUB, tag_val))
            return {"alias": alias[0][1]}
        elif self.SAY_AS in tag_val:
            interpret_as: List[Tuple] = re.findall(
                r"interpret-as\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val
            )
            if len(interpret_as) == 0:
                raise AttributeError(err_msg.format(self.SAY_AS, tag_val))
            return {"interpret-as": interpret_as[0][1]}
        elif self.PROSODY in tag_val:
            matches: List[Tuple] = re.findall(
                r"(\w+)\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val
            )
            if len(matches) == 0:
                raise AttributeError(err_msg.format(self.PROSODY, tag_val))
            return {m[0]: m[2] for m in matches}

        raise ValueError(
            f'Unable to extract attributes from unsupported tag: "{tag_val}"'
        )

    def _sub_consume(self, original: str) -> Dict[str, Any]:
        """
        Consumes the tokens present in the alias attribute of the sub tag.
        This function may be generalized for future implementations of other tags that may need specialized
        subconsumption.
        """

        # If we have consumed the entirety of the alias value, we have processed all of the incoming
        # originals for the currently active sub tag.
        whitespace: str = re.compile(r"^\s*", re.UNICODE)
        whitespace_len: int = len(
            re.match(whitespace, self._tag_metadata[self.SUB]["alias_view"]).group()
        )
        self._tag_metadata[self.SUB]["alias_view"] = self._tag_metadata[self.SUB][
            "alias_view"
        ][whitespace_len + len(original) :]

        self._tag_metadata[self.SUB]["alias_last_word"] = (
            len(self._tag_metadata[self.SUB]["alias_view"]) == 0
        )

        # We need to make corrections of the offsets here as the data has already been consumed at this point.
        len_token_consumption_bytes: int = utf8_byte_length(
            self._tag_stack[-1].get_data().strip()
        )
        n_bytes_consumed: int = self._n_bytes_consumed - len_token_consumption_bytes

        status: Dict = {
            "start_byte_offset": n_bytes_consumed,
            "end_byte_offset": self._n_bytes_consumed,
            "last_word": None,  # only relevant when consuming main SSML string
            "ssml_props": self._tag_stack[-1],
            "tag_metadata": self._tag_metadata[self._tag_stack[-1].tag_type],
        }

        if self._tag_metadata[self.SUB]["alias_last_word"]:
            # When custom consumption concludes, we reset these values.
            # sub->alias_view is already an empty string when we get here.
            self._reset_tag_metadata(self.SUB)

        return status

    def consume(self, original: str) -> Dict[str, Any]:
        """
        Consumes whitespace, tags and word. Returns consumption status which contains word byte offset data,
        SSML properties and additional required processing metadata.
        """
        if self._tag_metadata[self.SUB]["needs_sub_consumption"]:
            return self._sub_consume(original)

        len_token_consumption: int = len(original)
        len_token_consumption_bytes: int = utf8_byte_length(original)

        while True:
            # This loop handles the consumption of tags and whitespace. Afterwards, the word itself (original)
            # will be consumed.

            consumed: Match = re.match(self.SSML_WHITESPACE_REGEX, self._ssml_view)
            tag: Match = re.match(self.TAG_REGEX, self._ssml_view)
            tag_close: Match = re.match(self.TAG_CLOSE_REGEX, self._ssml_view)

            len_consumption: int = len(consumed.group()) if consumed else 0
            len_consumption_bytes: int = (
                utf8_byte_length(consumed.group()) if consumed else 0
            )

            self._n_bytes_consumed += len_consumption_bytes

            if tag_close:
                self._tag_stack.pop()
                self._update_data()
                self._tag_stack[-1].data = self._data
            elif tag:
                self._update_data()
                tag_val: str = tag.group().strip()
                if self.SPEAK in tag_val:
                    self._tag_stack.append(
                        SpeakProps(
                            tag_val=tag_val,
                            data=self._data,
                        )
                    )
                elif self.PHONEME in tag_val:
                    attrs: Dict[str, str] = self._extract_tag_attrs(tag_val)
                    self._tag_stack.append(
                        PhonemeProps(
                            tag_val=tag_val,
                            alphabet=attrs["alphabet"],
                            ph=attrs["ph"],
                            data=self._data,
                        )
                    )
                elif self.SUB in tag_val:
                    attrs: Dict[str, str] = self._extract_tag_attrs(tag_val)
                    self._tag_stack.append(
                        SubProps(
                            tag_val=tag_val,
                            alias=attrs["alias"],
                            data=self._data,
                        )
                    )

                    # The original token we receive here is the alias.
                    # We want to consume the data rather than the original token.
                    # Example:
                    #
                    #   <sub alias='Háskólanum í Reykjavík'>HR</sub>
                    #                                       ^
                    #                                       Consume this
                    #
                    # Because the alias tokens are normalized, we receive these tokens here as "original".
                    # We don't want to consume ssml_view using those tokens as we rather want the token
                    # offsets for the data ("HR" in this instance).
                    #
                    # If the alias value yielded multiple tokens during normalization, we need to subconsume
                    # each one. See self._sub_consume().

                    len_token_consumption = len(self._data.strip())
                    len_token_consumption_bytes = utf8_byte_length(self._data.strip())

                    alias: str = attrs["alias"].lstrip()[len(original) :].rstrip()
                    needs_sub_consumption: bool = len(alias) > 0
                    if needs_sub_consumption:
                        self._tag_metadata[self.SUB][
                            "needs_sub_consumption"
                        ] = needs_sub_consumption
                        self._tag_metadata[self.SUB]["alias_last_word"] = False
                        self._tag_metadata[self.SUB]["alias_view"] = alias
                elif self.SAY_AS in tag_val:
                    attrs: Dict[str, str] = self._extract_tag_attrs(tag_val)
                    self._tag_stack.append(
                        SayAsProps(
                            tag_val=tag_val,
                            interpret_as=attrs["interpret-as"],
                            data=self._data,
                        )
                    )
                elif self.PROSODY in tag_val:
                    attrs = self._extract_tag_attrs(tag_val)
                    self._tag_stack.append(
                        ProsodyProps(
                            tag_val=tag_val,
                            data=self._data,
                            rate=attrs.get("rate"),
                            pitch=attrs.get("pitch"),
                            volume=attrs.get("volume"),
                        )
                    )

            self._update_ssml_view(len_consumption)
            if not re.match(self.TAG_REGEX, self._ssml_view):
                # If the next part of ssml_view is NOT a tag, we have reached our word in the SSML which corresponds
                # to original. Therefore, there is no need to consume more tags or whitespace. We break out of the loop
                # and proceed to consume the word itself.
                break

        # If we have a tag after current word, that's the last word within current tag. This is relevant when we have
        # multiple words within a single phoneme tag.
        status: Dict = {
            "start_byte_offset": self._n_bytes_consumed,
            "end_byte_offset": self._n_bytes_consumed + len_token_consumption_bytes,
            "last_word": re.match(
                self.TAG_REGEX, self._ssml_view[len_token_consumption:]
            )
            != None,
            "ssml_props": self._tag_stack[-1],
            "tag_metadata": self._tag_metadata[self._tag_stack[-1].tag_type],
        }

        # Status package has been assembled, now we update the the status of the consumer before this function is called again for next token (word).
        self._update_ssml_view(len_token_consumption)
        self._n_bytes_consumed += len_token_consumption_bytes

        return status
