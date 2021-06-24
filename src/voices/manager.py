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
import typing

from .aws import VOICES as POLLY_VOICES
from .aws import PollyVoice
from .fastspeech import VOICES as FASTSPEECH_VOICES
from .fastspeech import FastSpeech2Synthesizer, FastSpeech2Voice
from .voice_base import VoiceBase


class VoiceManager:
    _synthesizers: typing.Dict[str, VoiceBase]
    _voices: typing.Dict[str, VoiceBase]
    _fastspeech_backend: FastSpeech2Synthesizer

    def __init__(self, synthesizers: typing.Dict[str, VoiceBase] = {}):
        if not synthesizers:
            # TODO(rkjaran): Remove this initialization here once we get rid of "Other"
            fastspeech_backend = FastSpeech2Synthesizer()
            self._synthesizers = {}
            self._synthesizers.update(
                {
                    voice.voice_id: FastSpeech2Voice(voice, backend=fastspeech_backend)
                    for voice in FASTSPEECH_VOICES
                }
            )
            self._synthesizers.update(
                {voice.voice_id: PollyVoice(voice) for voice in POLLY_VOICES}
            )
        else:
            self._synthesizers = synthesizers

    def __getitem__(self, key: str) -> VoiceBase:
        return self._synthesizers[key]

    def voices(self):
        return self._synthesizers.items()
