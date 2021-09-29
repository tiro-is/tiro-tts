# Copyright 2021 Tiro ehf.
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
from abc import ABC, abstractmethod, abstractproperty
from typing import Iterable, List, Literal, Optional, TextIO, Union


class OutputFormat:
    output_format: Literal["json", "mp3", "pcm", "ogg_vorbis"]
    supported_sample_rates: List[str]

    def __init__(self, output_format, supported_sample_rates):
        self.output_format = output_format
        self.supported_sample_rates = supported_sample_rates

    def __eq__(self, other) -> bool:
        if isinstance(other, tuple):
            return self.output_format == other[0] and (
                other[0] == "json" or other[1] in self.supported_sample_rates
            )
        return other.output_format == self.output_format

    def __repr__(self):
        return "<OutputFormat('{}', {})>".format(
            self.output_format, self.supported_sample_rates
        )

    @property
    def content_type(self):
        if self.output_format == "mp3":
            return "audio/mpeg"
        elif self.output_format == "ogg_vorbis":
            return "audio/ogg"
        elif self.output_format == "pcm":
            return "audio/x-wav"
        elif self.output_format == "json":
            return "application/x-json-stream"


class VoiceProperties:
    voice_id: str
    name: Optional[str]
    gender: Optional[Literal["Female", "Male"]]
    language_code: Optional[str]
    language_name: Optional[str]
    supported_output_formats: List[OutputFormat]

    def __init__(
        self,
        voice_id: str,
        name: Optional[str] = None,
        gender: Optional[Literal["Female", "Male"]] = None,
        language_code: Optional[str] = None,
        supported_output_formats=[],
    ):
        self.voice_id = voice_id
        self.name = name
        self.gender = gender
        self.language_code = language_code
        self.language_name = _LANGUAGE_NAMES[language_code] if language_code else None
        self.supported_output_formats = supported_output_formats


class VoiceBase(ABC):
    @abstractmethod
    def synthesize(self, text: str, **kwargs) -> Iterable[bytes]:
        return NotImplemented

    @abstractmethod
    def synthesize_from_ssml(self, ssml: str, **kwargs) -> Iterable[bytes]:
        return NotImplemented

    @abstractproperty
    def properties(self) -> VoiceProperties:
        return NotImplemented


_LANGUAGE_NAMES = {
    "is-IS": "Íslenska (Icelandic)",
    "en-US": "English",
}
