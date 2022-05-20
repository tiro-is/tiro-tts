import re
from typing import Dict, List, Pattern, Tuple

from regex import Match

from src.frontend.words import PhonemeProps, SSMLProps, SpeakProps, SubProps


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


class SSMLConsumer:
    # General consumption variables
    _ssml: str
    _ssml_view: str
    _data: str

    _n_bytes_consumed: int

    _tag_specific_data: Dict
    _tag_stack: List[SSMLProps]

    TAG_REGEX: Pattern
    TAG_CLOSE_REGEX: Pattern
    SSML_WHITESPACE_REGEX: Pattern

    # Custom tag variables
    tag_custom_consumption_sub: bool
    tag_sub_alias_view: str

    def __init__(self, ssml) -> None:
        # General consumption variables
        self._ssml_view = ssml
        self._data = ""

        self._n_bytes_consumed = 0

        self._tag_specific_data = None
        self._tag_stack = []

        TAG_PATTERN: str = r"<(\"[^\"]*\"|'[^']*'|[^'\">])*>"
        TAG_CLOSE_PATTERN: str = r"^\s*<\s*/\s*.*?\s*>"
        TAG_WHITESPACE_PATTERN: str = f"^\s*({TAG_PATTERN})?\s*"
        self.TAG_REGEX = re.compile(f"^\s*{TAG_PATTERN}", re.UNICODE)
        self.TAG_CLOSE_REGEX = re.compile(TAG_CLOSE_PATTERN, re.UNICODE)
        self.SSML_WHITESPACE_REGEX = re.compile(TAG_WHITESPACE_PATTERN, re.UNICODE)

        # Custom tag variables
        self.tag_sub_alias_view = ""
        self.tag_custom_consumption_sub = False

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
        if "phoneme" in tag_val:
            alphabet: List[Tuple] = re.findall(
                r"alphabet\s*=\s*(\"|'{1}(x-sampa|ipa)(\"|'){1})", tag_val
            )
            ph: List[Tuple] = re.findall(r"ph\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val)

            if len(alphabet) == 0 or len(ph) == 0:
                raise AttributeError(err_msg.format("phoneme", tag_val))
            if len(alphabet[0]) < 2 or len(ph[0]) < 2:
                raise AttributeError(err_msg.format("phoneme", tag_val))

            return {
                "alphabet": alphabet[0][1],
                "ph": ph[0][1],
            }
        elif "sub" in tag_val:
            alias: List[Tuple] = re.findall(r"alias\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val)
            if len(alias) == 0:
                raise AttributeError(err_msg.format("sub", tag_val))
            return { "alias": alias[0][1] }

        raise ValueError(
            f'Unable to extract attributes from unsupported tag: "{tag_val}"'
        )

    def consume(self, original: str) -> Dict:
        """
        Consumes whitespace, tags and word. Returns consumption status which contains word byte offset data
        and SSML properties.
        """
        if self.tag_custom_consumption_sub:
            # If we have consumed the entirety of the alias value, we have processed all of the incoming
            # originals for the currently active sub tag.
            whitespace: str = re.compile(r"^\s*", re.UNICODE)
            whitespace_len: int = len(re.match(whitespace, self.tag_sub_alias_view).group())
            self.tag_sub_alias_view = self.tag_sub_alias_view[whitespace_len + len(original):]

            self._tag_specific_data["sub"]["alias_last_word"] = len(self.tag_sub_alias_view) == 0

            status: Dict = {
                "start_byte_offset": self._tag_specific_data["sub"]["start_byte_offset"],
                "end_byte_offset": self._tag_specific_data["sub"]["end_byte_offset"],
                "last_word": None,                                                          # last_word is for last word in data, so we don't care about that information here.
                "ssml_props": self._tag_stack[-1],
                "tag_specific": self._tag_specific_data,
            }

            if self._tag_specific_data["sub"]["alias_last_word"]:
                # When custom consumption concludes, we reset these values.
                # self.tag_sub_alias_view is already an empty string when we get here.
                self._tag_specific_data = None
                self.tag_custom_consumption_sub = False

            return status

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
                if "speak" in tag_val:
                    self._tag_stack.append(
                        SpeakProps(
                            tag_val=tag_val,
                            data=self._data,
                        )
                    )
                elif "phoneme" in tag_val:
                    attrs: Dict[str, str] = self._extract_tag_attrs(tag_val)
                    self._tag_stack.append(
                        PhonemeProps(
                            tag_val=tag_val,
                            alphabet=attrs["alphabet"],
                            ph=attrs["ph"],
                            data=self._data,
                        )
                    )
                elif "sub" in tag_val:
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
                    len_token_consumption = len(self._data)
                    len_token_consumption_bytes = utf8_byte_length(self._data)
                    
                    self.tag_custom_consumption_sub = self._tag_stack[-1].is_multi(alternate_data=attrs["alias"])
                    if self.tag_custom_consumption_sub:
                        self._tag_specific_data = {
                            "sub": {
                                "start_byte_offset": self._n_bytes_consumed,                                # Sleppa. Við consume-um ekkert meir fyrr en sub er lokið
                                "end_byte_offset": self._n_bytes_consumed + len_token_consumption_bytes,    # Sleppa. Getum alltaf sótt len_token_consumption_bytes úr len(tag_stack[-1]._data)
                                "alias_last_word": False,
                            }
                        }
                        self.tag_sub_alias_view = attrs["alias"][len(original):]

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
            "last_word": re.match(self.TAG_REGEX, self._ssml_view[len_token_consumption :]) != None,
            "ssml_props": self._tag_stack[-1],
            "tag_specific": self._tag_specific_data,
        }

        # Status package has been assembled, now we update the the status of the consumer before this function is called again for next token (word).
        self._update_ssml_view(len_token_consumption)
        self._n_bytes_consumed += len_token_consumption_bytes

        return status
