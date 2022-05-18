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
import contextlib
from typing import Iterable

from boto3 import Session
from flask import current_app

from .voice_base import OutputFormat, VoiceBase, VoiceProperties


class PollySession:
    @classmethod
    def get_client(cls):
        session = getattr(
            cls,
            "_session",
            Session(
                aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
                region_name=current_app.config["AWS_REGION"],
            ),
        )
        return getattr(cls, "_polly", session.client("polly"))


class PollyVoice(VoiceBase):
    _properties: VoiceProperties

    def __init__(self, properties: VoiceProperties):
        """Initialize a fixed voice with a Polly backend"""
        self._properties = properties

    def _synthesize_speech(self, *args, **kwargs):
        return PollySession.get_client().synthesize_speech(*args, **kwargs)

    def synthesize(self, text: str, ssml: bool = False, **kwargs) -> Iterable[bytes]:
        resp = self._synthesize_speech(**kwargs)
        if "AudioStream" in resp:
            with contextlib.closing(resp["AudioStream"]) as stream:
                content = stream.read()
            # TODO(rkjaran): Chunk this
            yield content

    @property
    def properties(self) -> VoiceProperties:
        return self._properties


_MP3_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_OGG_VORBIS_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_PCM_SAMPLE_RATES = ["8000", "16000", "22050"]
SUPPORTED_OUTPUT_FORMATS = [
    OutputFormat(output_format="mp3", supported_sample_rates=_MP3_SAMPLE_RATES),
    OutputFormat(output_format="pcm", supported_sample_rates=_PCM_SAMPLE_RATES),
    OutputFormat(
        output_format="ogg_vorbis", supported_sample_rates=_OGG_VORBIS_SAMPLE_RATES
    ),
    OutputFormat(output_format="json", supported_sample_rates=[]),
]
