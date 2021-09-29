import re
from typing import Tuple

WHITESPACE_REGEX = re.compile(r"^\s+", re.UNICODE)
WHITESPACE_REGEX_BYTES = re.compile(rb"^\s+")


def utf8_byte_length(text: str) -> int:
    return len(text.encode("utf-8"))


def consume_whitespace(text: str) -> Tuple[int, int]:
    """Consume whitespace prefix

    Returns:
      A tuple of the number of characters consumed, and the number of bytes consumed.

    """
    m = re.match(WHITESPACE_REGEX, text)
    if m:
        return len(m.group()), utf8_byte_length(m.group())
    return 0, 0


def consume_whitespace_bytes(data: bytes) -> int:
    """Consume whitespace prefix

    Returns:
      The number of bytes consumed.

    """
    m = re.match(WHITESPACE_REGEX_BYTES, data)
    if m:
        return len(m.group())
    return 0
