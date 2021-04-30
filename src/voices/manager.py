import typing
from . import VoiceBase, OutputFormat, aws, fastspeech
from .aws import PollyVoice, VOICES as POLLY_VOICES
from .fastspeech import (
    FastSpeech2Synthesizer,
    FastSpeech2Voice,
    VOICES as FASTSPEECH_VOICES,
)


class VoiceManager:
    _synthesizers: typing.Dict[str, VoiceBase] = {}
    _voices: typing.Dict[str, VoiceBase]

    def __init__(self, synthesizers: typing.Dict[str, VoiceBase] = {}):
        if not synthesizers:
            self._synthesizers.update(
                {voice.voice_id: FastSpeech2Voice(voice) for voice in FASTSPEECH_VOICES}
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
