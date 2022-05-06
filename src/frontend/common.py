import re
from typing import Dict, List, Pattern, Tuple


from src.frontend.words import PhonemeProps, SSMLProps, SpeakProps

WHITESPACE_REGEX = re.compile(r"^\s+", re.UNICODE)
WHITESPACE_REGEX_BYTES = re.compile(rb"^\s+")

SSML_WHITESPACE_REGEX = re.compile(r"^\s*(<(\"[^\"]*\"|'[^']*'|[^'\">])*>)* ?", re.UNICODE)
SSML_WHITESPACE_REGEX_BYTES = re.compile(rb"^\s*(<(\"[^\"]*\"|'[^']*'|[^'\">])*>)* ?")

def utf8_byte_length(text: str) -> int:
    return len(text.encode("utf-8"))


def consume_whitespace(text: str, ssml: bool = False) -> Tuple[int, int]:
    """Consume non-text (whitespace and/or SSML tags) prefix

    Returns:
      A tuple of the number of characters consumed, and the number of bytes consumed.

    """
    m = re.match(SSML_WHITESPACE_REGEX if ssml else WHITESPACE_REGEX, text)
    if m:
        return len(m.group()), utf8_byte_length(m.group())
    return 0, 0


def consume_whitespace_bytes(data: bytes, ssml: bool = False) -> int:
    """Consume non-text (whitespace and/or SSML tags) prefix

    Returns:
      The number of bytes consumed.

    """
    m = re.match(SSML_WHITESPACE_REGEX_BYTES if ssml else WHITESPACE_REGEX_BYTES, data)
    if m:
        return len(m.group())
    return 0


class SSMLConsumer:
    _ssml: str
    _ssml_view: str
    _data: str

    _n_bytes_consumed: int

    _tag_stack: List[SSMLProps]

    TAG_REGEX: Pattern
    TAG_CLOSE_REGEX: Pattern
    SSML_WHITESPACE_REGEX: Pattern

    def __init__(self, ssml) -> None:
        #TODO(Smári): Have an instance of SSMLParser as a class variable. Use it here to sanitize markup.

        self._ssml = ssml
        self._ssml_view = ssml
        self._data = ""

        self._n_bytes_consumed = 0

        self._tag_stack = []
        
        TAG_PATTERN: str = r"<(\"[^\"]*\"|'[^']*'|[^'\">])*>"
        TAG_CLOSE_PATTERN: str = r"^\s*<\s*/\s*.*?\s*>"
        TAG_WHITESPACE_PATTERN: str = f"^\s*({TAG_PATTERN})* ?"
        self.TAG_REGEX = re.compile(f"^\s*{TAG_PATTERN}", re.UNICODE)
        self.TAG_CLOSE_REGEX = re.compile(TAG_CLOSE_PATTERN, re.UNICODE)
        self.SSML_WHITESPACE_REGEX = re.compile(TAG_WHITESPACE_PATTERN, re.UNICODE)

    def _update_ssml_view(self, len_consumption, len_original) -> None:
        self._ssml_view = self._ssml_view[len_consumption + len_original :]

    def _update_data(self) -> None:
        """Sets _data's value to all text within current tag"""
        self._data = re.findall(r">(\s?.*?\s?)<", self._ssml_view)[0]

    def _extract_tag_attrs(self, tag_val) -> Dict[str, str]:
        """Extracts tag attributes from tags."""
        
        if "phoneme" in tag_val:
            alphabet: str = re.findall(r"alphabet\s*=\s*(\"|'{1}(x-sampa|ipa)(\"|'){1})", tag_val)
            ph: str = re.findall(r"ph\s*=\s*(\"|'{1}(.*?)(\"|'){1})", tag_val)

            # Note: This should already be sanitized by SSMLPArser during instance initilization of this class.
            err_msg: str = "phoneme tag did not supply the required attributes!"
            if len(alphabet) == 0 or len(ph) == 0:
                raise Exception(err_msg)
            if len(alphabet[0]) < 2 or len(ph[0]) < 2:
                raise Exception(err_msg)

            return {
                "alphabet": alphabet[0][1],
                "ph": ph[0][1],
            }

        raise Exception(f"Unable to extract attributes from unsupported tag: \"{tag_val}\"")
            

    def consume(self, original: str) -> Dict:
        consumed = re.match(self.SSML_WHITESPACE_REGEX, self._ssml_view)
        tag = re.match(self.TAG_REGEX, self._ssml_view)
        tag_close = re.match(self.TAG_CLOSE_REGEX, self._ssml_view)

        len_consumption = len(consumed.group()) if consumed else 0
        len_consumption_bytes = utf8_byte_length(consumed.group()) if consumed else 0
        len_token_bytes = utf8_byte_length(original)

        if tag_close:
            self._tag_stack.pop()
            self._update_data()
            self._tag_stack[-1].data = self._data
        elif tag:
            self._update_data()
            tag_val: str = tag.group().strip()
            if "speak" in tag_val:                              #TODO(Smári): Make these checks safer
                self._tag_stack.append(SpeakProps(self._data))
            elif "phoneme" in tag_val:
                attrs: Dict[str, str] = self._extract_tag_attrs(tag_val)
                self._tag_stack.append(
                    PhonemeProps(
                        alphabet=attrs["alphabet"],
                        ph=attrs["ph"],
                        data=self._data,
                    )
                )

        self._update_ssml_view(len_consumption, len(original))
        self._n_bytes_consumed += len_consumption_bytes
        self._tag_stack[-1].data_last_word = (re.match(self.TAG_CLOSE_REGEX, self._ssml_view) != None)

        status: Dict = {
            "start_byte_offset": self._n_bytes_consumed,
            "end_byte_offset": self._n_bytes_consumed + len_token_bytes,
            "ssml_props": self._tag_stack[-1],
        }
        self._n_bytes_consumed += utf8_byte_length(original)

        return status
