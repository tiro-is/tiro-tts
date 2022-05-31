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

# This parser provides the following service:
#   1) Tag stripping (text isolation)
#   2) Markup sanitization:
#       a) Are all tags matched by closing tags of the same type?
#       b) Do all tag attributes fullfil their requirements?
#       c) Are there any tags with no text where it must be present?


class SSMLValidationException(Exception):
    ...


class OldSSMLParser(HTMLParser):
    _ALLOWED_TAGS = ["speak", "phoneme", "sub", "say-as"]
    _first_tag_seen: bool
    _tag_stack: List[str]
    _text: List[str]

    # Tag specific variables

    # <sub>

    # When we isolate the text (by removing the tags) from the SSML, we must take a special care of text extracted
    # from <sub> tags. Usually we only want to extract the data (>the text between the opening and closing tags<) but
    # for <sub> tags, we rather want the text that the alias attribute defines in the opening tag. Because
    # we don't have access to this information (the alias attribute value) in handle_data(), we put it into this variable
    # while in handle_starttag() and keep it there until it is needed in a subsequent call to handle_data(). That way,
    # we are able to substitute the >data value< for the alias value.
    # This is done because we normalize the tag-stripped text and that text must contain the alias rather than the
    # data.
    _sub_alias: str

    # <say-as>
    _SAY_AS_SUPPORTED_INTRPRT_VALS: str = ["characters", "spell-out"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._first_tag_seen = False
        self._tag_stack = []
        self._text = []

        self._sub_alias = ""

    def _check_first_tag(self, tag):
        if not self._first_tag_seen:
            if tag != "speak":
                raise SSMLValidationException("Start tag is not <speak>")
            self._first_tag_seen = True

    def handle_starttag(self, tag, attrs):
        self._check_first_tag(tag)
        if len(self._tag_stack) == 2:
            # We are about to push a third tag to the stack. If there are already two, the SSML
            # contains a 3-level (perhaps deeper!) nesting which is illegal.
            raise SSMLValidationException("Illegal SSML! Maximum nesting level is 2.")

        if tag not in OldSSMLParser._ALLOWED_TAGS:
            raise SSMLValidationException(
                "Unsupported tag encountered: '{}'".format(tag)
            )

        if tag in self._tag_stack:
            # If tag type is already in the stack, that means that we are adding some type of tag
            # nested within itself, which is illegal.
            # Example:
            #           "<speak>Halló, hvað segir<speak> þú</speak> gott?</speak>"
            raise SSMLValidationException(
                "Illegal SSML! Nesting a tag of the same type as a higher level tag not allowed."
            )

        attrs_map = dict(attrs)
        if tag == "speak":
            if len(attrs_map) > 0:
                raise SSMLValidationException(
                    "Illegal SSML! speak tag does not take any attributes!"
                )
        elif tag == "phoneme":
            if attrs_map.get("alphabet") != "x-sampa" or "ph" not in attrs_map:
                raise SSMLValidationException(
                    "'phoneme' tag has to have 'alphabet' and 'ph' attributes using "
                    "supported alphabets"
                )
            # A check whether the phone sequence (ph) is valid, is made at a later stage in PhonemeProps:get_phone_sequence
            # during consumption.
        elif tag == "sub":
            if len(attrs_map) == 0 or "alias" not in attrs_map:
                raise SSMLValidationException(
                    "Illegal SSML! sub tag requires the 'alias' attribute."
                )
            self._sub_alias = attrs_map.get("alias")
        elif tag == "say-as":
            if len(attrs_map) == 0 or "interpret-as" not in attrs_map:
                # TODO(Smári): Add checks for possible other attributes that are required when
                # "interpret-as" is something such as "date", then the "format" attribute is required.
                # We should probably too add a constant list of allowed attribute values as they are
                # quite many for this tag.
                raise SSMLValidationException(
                    "Illegal SSML! <say-as> tag requires the 'interpret-as' attribute."
                )

            interpret_as_val: str = attrs_map.get("interpret-as")
            if interpret_as_val not in self._SAY_AS_SUPPORTED_INTRPRT_VALS:
                raise SSMLValidationException(
                    'Illegal SSML! Encountered unsupported "interpret-as" attribute value in <say-as> tag: {}'.format(
                        interpret_as_val
                    )
                )

        self._tag_stack.append(tag)

    def handle_endtag(self, tag):
        open_tag = self._tag_stack.pop()
        if open_tag != tag:
            raise SSMLValidationException(
                "Invalid closing tag '{}' for '{}'".format(tag, open_tag)
            )

    def handle_data(self, data):
        # Raise a SSMLValidationException if we haven't seen the initial <speak> tag
        self._check_first_tag("")

        if len(self._tag_stack) == 0:
            # An empty tag queue means that all tags have been popped and their contents processed.
            # If, at this point, we enter this function with some data, it must be outside of the
            # markup, coming after the final speak tag. That is illegal.
            # _check_first_tag() makes sure this doesn't happen in the other end (text outside of markup
            # before the first speak tag).
            raise SSMLValidationException(
                "Illegal SSML! All text must be contained within SSML tags."
            )
        if self._tag_stack[-1] == "sub":
            data = self._sub_alias

        self._text.append(data)

    def get_text(self) -> str:
        """
        Removes the SSML markup and returns a string containing only the text.

        Return example:
          "Halló aa" if the input SSML was "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"
        """

        if len(self._tag_stack) > 0:
            raise SSMLValidationException("Not all tags were closed, malformed SSML.")

        text: str = "".join(self._text)
        if len(text) == 0 or text.isspace():
            raise SSMLValidationException("The SSML did not contain any text!")
        return text
