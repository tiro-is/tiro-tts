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
from html.parser import HTMLParser
from typing import List

from src.frontend.phonemes import align_ipa_from_xsampa
from src.frontend.words import PhonemeProps, SpeakProps, Word

# TODO(Smári): Does this parser handle illegal input like speak tags within speak tags and phoneme tags within phoneme tags?

# This parser provides the following service:
#   1) Tag stripping (text isolation)
#   2) Markup sanitization:
#       a) Are all tags matched by closing tags of the same type?
#       b) Do all tag attributes fullfil their requirements?
#       c) Are there any tags with no text where it must be present?

class OldSSMLParser(HTMLParser):
    _ALLOWED_TAGS = ["speak", "phoneme"]
    _first_tag_seen: bool
    _tags_queue: List[str]
    _text: List[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._first_tag_seen = False
        self._tags_queue = []
        self._text = []

    def _check_first_tag(self, tag):
        if not self._first_tag_seen:
            if tag != "speak":
                raise ValueError("Start tag is not <speak>")
            self._first_tag_seen = True

    def handle_starttag(self, tag, attrs):
        self._check_first_tag(tag)

        if tag not in OldSSMLParser._ALLOWED_TAGS:
            raise ValueError("Unsupported tag encountered: '{}'".format(tag))

        if tag == "phoneme":
            #TODO(Smári): Raise error if ph contains invalid or empty phone sequence.

            attrs_map = dict(attrs)
            if attrs_map.get("alphabet") != "x-sampa" or "ph" not in attrs_map:
                raise ValueError(
                    "'phoneme' tag has to have 'alphabet' and 'ph' attributes using "
                    "supported alphabets"
                )
        self._tags_queue.append(tag)

    def handle_endtag(self, tag):
        open_tag = self._tags_queue.pop()
        if open_tag != tag:
            raise ValueError("Invalid closing tag '{}' for '{}'".format(tag, open_tag))

    def handle_data(self, data):
        # Raise a ValueError if we haven't seen the initial <speak> tag
        self._check_first_tag("")

        active_tag: str = self._tags_queue[-1]
        if active_tag == "speak":
            if data.isspace() or len(data) == 0:
                raise ValueError("speak tags must contain text!")

        self._text.append(data)

    def get_text(self) -> str:
        """
        Removes the SSML markup and returns a string containing only the text.

        Return example:
          "Halló aa" if the input SSML was "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"
        """

        if len(self._tags_queue) > 0:
            raise ValueError("Not all tags were closed, malformed SSML.")
        
        text: str = "".join(self._text)
        if len(text) == 0:
            raise ValueError("The SSML did not contain any text!")
        return text
