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
from src.frontend.words import Word

# TODO(Smári): Does this parser handle illegal input like speak tags within speak tags and phoneme tags within phoneme tags?

class OldSSMLParser(HTMLParser):
    _ALLOWED_TAGS = ["speak", "phoneme"]
    _first_tag_seen: bool
    _tags_queue: List[str]
    _words: List[Word]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._first_tag_seen = False
        self._tags_queue = []
        self._words = []

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
            attrs_map = dict(attrs)
            if attrs_map.get("alphabet") != "x-sampa" or "ph" not in attrs_map:
                raise ValueError(
                    "'phoneme' tag has to have 'alphabet' and 'ph' attributes using "
                    "supported alphabets"
                )
            self._words.append(
                Word(
                    phone_sequence=align_ipa_from_xsampa(attrs_map["ph"])
                        .split()
                )
            )
        self._tags_queue.append(tag)

    def handle_endtag(self, tag):
        open_tag = self._tags_queue.pop()
        if open_tag != tag:
            raise ValueError("Invalid closing tag '{}' for '{}'".format(tag, open_tag))

    def handle_data(self, data):
        # Raise a ValueError if we haven't seen the initial <speak> tag
        self._check_first_tag("")

        if self._tags_queue[-1] != "phoneme":
            for word in data.split():
                self._words.append(
                    Word(original_symbol=word)
                )
        else:
            self._words[-1].original_symbol = data.strip()


    def get_words(self) -> List[Word]:
        """
        Get list of Words that represent the data extracted from the SSML.

        Returns:
          A list of Words where each Word contains a word from the SSML as original_symbol.
          <phoneme> enclosed text is given a special treatment where its data is set as a Word's original_symbol but
          the phoneme tag's ph attribute value is set as the Word's phone_sequence.
          E.g.:
          [Word(original_symbol="Halló"), Word(original_symbol="aa", phone_sequence="a")] if the input SSML was "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"

        """
        if len(self._tags_queue) > 0:
            raise ValueError("Not all tags were closed, malformed SSML.")
        return self._words

    def get_text(self) -> str:
        """
        Removes the SSML markup and returns a string containing only the text.

        Return example:
          "Halló aa" if the input SSML was "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"
        """
        return " ".join([word.original_symbol for word in self._words])
