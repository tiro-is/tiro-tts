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
from pathlib import Path
from typing import Dict, List, Literal, Optional, TextIO, Union

import google.protobuf.text_format

from proto.tiro.tts import voice_pb2
from src.frontend.grapheme_to_phoneme import (
    ComposedTranslator,
    GraphemeToPhonemeTranslatorBase,
    IceG2PTranslator,
    LangID,
    LexiconGraphemeToPhonemeTranslator,
    SequiturGraphemeToPhonemeTranslator,
)
from src.frontend.lexicon import SimpleInMemoryLexicon
from src.frontend.normalization import (
    BasicNormalizer,
    GrammatekNormalizer,
    NormalizerBase,
)

from . import aws, fastspeech
from .aws import PollyVoice
from .fastspeech import FastSpeech2Synthesizer, FastSpeech2Voice
from .voice_base import VoiceBase, VoiceProperties


class VoiceManager:
    _synthesizers: Dict[str, VoiceBase]
    _phonetizers: Dict[str, GraphemeToPhonemeTranslatorBase]

    def __init__(
        self,
        synthesizers: Dict[str, VoiceBase],
        phonetizers: Dict[str, GraphemeToPhonemeTranslatorBase],
    ):
        self._phonetizers = phonetizers
        self._synthesizers = synthesizers

    @staticmethod
    def from_pbtxt(pbtxt_path: Path) -> "VoiceManager":
        with pbtxt_path.open("rt") as pb_obj:
            synthesis_set: voice_pb2.SynthesisSet = google.protobuf.text_format.Parse(
                pb_obj.read(), voice_pb2.SynthesisSet()
            )

        phonetizers: Dict[str, GraphemeToPhonemeTranslatorBase] = {}
        for phonetizer in synthesis_set.phonetizers:
            phonetizers[phonetizer.name] = ComposedTranslator(
                *(
                    _translator_from_pb(translator, phonetizer.language_code)
                    for translator in phonetizer.translators
                )
            )

        normalizers: Dict[str, NormalizerBase] = {}
        for normalizer in synthesis_set.normalizers:
            normalizers[normalizer.name] = _normalizer_from_pb(normalizer)
        if not normalizers:
            normalizers["fallback"] = BasicNormalizer()

        synthesizers: Dict[str, VoiceBase] = {}
        for voice in synthesis_set.voices:
            props = VoiceProperties(
                voice_id=voice.voice_id,
                name=voice.display_name,
                gender=_gender_pb_as_str(voice.gender),
                language_code=voice.language_code,
            )
            backend_name = voice.WhichOneof("backend")
            if backend_name == "fs2melgan":
                props.supported_output_formats = fastspeech.SUPPORTED_OUTPUT_FORMATS
                fs = FastSpeech2Voice(
                    properties=props,
                    backend=FastSpeech2Synthesizer(
                        melgan_vocoder_path=_parse_uri(voice.fs2melgan.melgan_uri),
                        fastspeech_model_path=_parse_uri(
                            voice.fs2melgan.fastspeech2_uri
                        ),
                        phonetizer=phonetizers[voice.fs2melgan.phonetizer_name],
                        normalizer=normalizers[
                            voice.fs2melgan.normalizer_name or "fallback"
                        ],
                    ),
                )
                synthesizers[props.voice_id] = fs
            elif backend_name == "polly":
                props.supported_output_formats = aws.SUPPORTED_OUTPUT_FORMATS
                synthesizers[props.voice_id] = PollyVoice(properties=props)
            else:
                raise ValueError("Unsupported backend {}".format(backend_name))

        return VoiceManager(synthesizers=synthesizers, phonetizers=phonetizers)

    def __getitem__(self, key: str) -> VoiceBase:
        return self._synthesizers[key]

    def voices(self):
        return self._synthesizers.items()


def _gender_pb_as_str(
    gender_pb: voice_pb2.Voice.Gender,
) -> Optional[Literal["Male", "Female"]]:
    if gender_pb == voice_pb2.Voice.MALE:
        return "Male"
    elif gender_pb == voice_pb2.Voice.FEMALE:
        return "Female"
    else:
        return None


def _alphabet_pb_as_str(alphabet_pb: voice_pb2.Alphabet) -> Literal["x-sampa", "ipa"]:
    """Convert voice_pb2.Alphabet enum to string, defaulting to x-sampa

    Raises:
      ValueError on unsupported enum value
    """
    if alphabet_pb == voice_pb2.Alphabet.IPA:
        return "ipa"
    elif (
        alphabet_pb == voice_pb2.Alphabet.XSAMPA
        or alphabet_pb == voice_pb2.Alphabet.UNSPECIFIED_ALPHABET
    ):
        return "x-sampa"
    else:
        raise ValueError("Unsupported alphabet")


def _parse_uri(uri: str) -> Path:
    if uri[0:7] != "file://":
        raise ValueError("Only file:// URIs are (currently) supported.")
    return Path(uri[7:])


def _translator_from_pb(
    pb: voice_pb2.Phonetizer.Translator,
    language_code: str,
) -> GraphemeToPhonemeTranslatorBase:
    model_kind = pb.WhichOneof("model_kind")
    if model_kind == "lexicon":
        return LexiconGraphemeToPhonemeTranslator(
            {
                LangID(language_code): SimpleInMemoryLexicon(
                    lex_path=_parse_uri(pb.lexicon.uri),
                    alphabet=_alphabet_pb_as_str(pb.lexicon.alphabet),
                )
            }
        )
    elif model_kind == "sequitur":
        return SequiturGraphemeToPhonemeTranslator(
            lang_model_paths={
                LangID(pb.sequitur.language_code): _parse_uri(pb.sequitur.uri)
            }
        )
    elif model_kind == "ice_g2p":
        if language_code != "is-IS":
            raise ValueError("Unsupported language for ice-g2p")

        if pb.ice_g2p.alphabet not in (
            voice_pb2.Alphabet.XSAMPA,
            voice_pb2.Alphabet.XSAMPA_WITH_STRESS_AND_SYLLABIFICATION,
        ):
            raise ValueError("Unsupported alphabet for ice-g2p")

        return IceG2PTranslator()
    else:
        raise ValueError("Unsupported translator type.")


def _normalizer_from_pb(pb: voice_pb2.Normalizer) -> NormalizerBase:
    kind = pb.WhichOneof("kind")
    if kind == "basic":
        return BasicNormalizer()
    elif kind == "grammatek":
        return GrammatekNormalizer(address=pb.grammatek.address)
    else:
        raise ValueError("Unsupported normalizer type.")
