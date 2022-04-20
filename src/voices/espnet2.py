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
import json
import os
import re
import string
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np
import resampy
import tokenizer
import torch
from espnet2.bin.tts_inference import Text2Speech
from espnet2.torch_utils.device_funcs import to_device as espnet2_to_device
from espnet_model_zoo.downloader import ModelDownloader
from flask import current_app

from src import ffmpeg
from src.frontend.grapheme_to_phoneme import GraphemeToPhonemeTranslatorBase
from src.frontend.normalization import BasicNormalizer, NormalizerBase
from src.frontend.phonemes import Alphabet
from src.frontend.ssml import OldSSMLParser as SSMLParser
from src.frontend.words import WORD_SENTENCE_SEPARATOR, Word, preprocess_sentences

from .utils import wavarray_to_pcm
from .voice_base import OutputFormat, VoiceBase, VoiceProperties


class Espnet2Synthesizer:
    """Synthesizer backend for ESPNET2 trained voices.

    The backend should be able to run ESPNET2 voices compatible with the Text2Speech
    inference class. The models are loaded either from the HuggingFace Model Zoo or
    directly from a Zip archive on the file system. The vocoder for the model is a Zip
    archive loaded from the local file system which contains a Text2Speech compatible
    vocoder model in a *.pkl file and its config in a *.yaml file.


    Example:

    >>> backend = Espnet2Synthesizer(
    >>>     model_uri="file://external/test_models/dilja/espnet2.zip",
    >>>     vocoder_uri="file://external/test_models/universal/pwg.zip",
    >>>     phonetizer=IceG2PTranslator(),
    >>>     normalizer=BasicNormalizer(),
    >>>     alphabet="x-sampa+syll+stress",
    >>> )
    >>> ...

    """

    _phonetizer: GraphemeToPhonemeTranslatorBase
    _normalizer: NormalizerBase
    _tts_internal: Text2Speech
    _phoneme_map: Dict[str, int]
    _alphabet: Alphabet

    def __init__(
        self,
        model_uri: str,
        vocoder_uri: Optional[str],
        phonetizer: GraphemeToPhonemeTranslatorBase,
        normalizer: NormalizerBase,
        alphabet: Alphabet,
    ):
        self._phonetizer = phonetizer
        self._normalizer = normalizer
        self._alphabet = alphabet

        with tempfile.TemporaryDirectory() as tmpdir:
            if not (model_uri.startswith("zoo://") or model_uri.startswith("file://")):
                raise ValueError("Invalid URI scheme")
            try:
                name_or_path = model_uri.split("://")[1]
                model_info = ModelDownloader(tmpdir).download_and_unpack(name_or_path)

                if vocoder_uri:
                    if not vocoder_uri.startswith("file://"):
                        raise ValueError(
                            f"Unsupported URI scheme for vocoder: '{vocoder_uri}'"
                        )

                    vocoder_path = vocoder_uri.split("://")[1]
                    with zipfile.ZipFile(vocoder_path, "r") as vocoder_zip:
                        vocoder_file = [
                            f for f in vocoder_zip.namelist() if f.endswith(".pkl")
                        ][0]
                        vocoder_config = [
                            f
                            for f in vocoder_zip.namelist()
                            if f.endswith(".yaml") or f.endswith(".yml")
                        ][0]
                        vocoder_zip.extractall(tmpdir, [vocoder_file, vocoder_config])

                self._tts_internal = Text2Speech(
                    train_config=model_info["train_config"],
                    model_file=model_info["model_file"],
                    vocoder_config=Path(tmpdir) / vocoder_config
                    if vocoder_uri
                    else None,
                    vocoder_file=Path(tmpdir) / vocoder_file if vocoder_uri else None,
                    speed_control_alpha=1.0,  # is this only an initialization option?
                )
                self._phoneme_map = {
                    phn: idx
                    for idx, phn in enumerate(self._tts_internal.train_args.token_list)
                }
            except IndexError:
                raise ValueError("Missing model path or name")
            except zipfile.BadZipFile:
                raise ValueError("Vocoder must be a Zip archive")

    def synthesize(
        self,
        text: str,
        emit_speech_marks: bool = False,
        sample_rate: int = 22050,
        # TODO(rkjaran): remove once we support normalization with SSML in a generic
        #   way. Also remove it from FastSpeech2Voice
        handle_embedded_phonemes: bool = False,
    ) -> Iterable[bytes]:
        if emit_speech_marks:
            raise NotImplementedError("This backend doesn't support speech marks!")

        normalize_fn = (
            self._normalizer.normalize
            if not handle_embedded_phonemes
            else BasicNormalizer().normalize
        )

        def phonetize_fn(*args, **kwargs):
            return self._phonetizer.translate_words(
                *args, **kwargs, alphabet=self._alphabet
            )

        for segment_words, phone_seq, phone_counts in preprocess_sentences(
            text, normalize_fn, phonetize_fn
        ):
            batch = espnet2_to_device(
                {
                    "text": self._tts_internal.preprocess_fn(
                        "<dummy>", {"text": " ".join(phone_seq)}
                    )["text"]
                }
            )
            out = self._tts_internal.model.inference(
                **batch, **self._tts_internal.decode_conf
            )
            wav = self._tts_internal.vocoder(out["feat_gen"])

            max_wav_value: float = 32768.0
            wav = wav * (20000 / torch.max(torch.abs(wav)))
            wav = wav.clamp(min=-max_wav_value, max=max_wav_value - 1)
            wav = wav.to(dtype=torch.int16)

            yield wavarray_to_pcm(
                wav.cpu().numpy(),
                src_sample_rate=self._tts_internal.fs,
                dst_sample_rate=sample_rate,
            )


class Espnet2Voice(VoiceBase):
    _backend: Espnet2Synthesizer
    _properties: VoiceProperties

    def __init__(self, properties: VoiceProperties, backend):
        """Initialize a fixed voice with a Espnet2 backend."""
        self._backend = backend
        self._properties = properties

    def _is_valid(self, **kwargs) -> bool:
        # Some sanity checks
        try:
            return (
                _is_output_format_supported(
                    kwargs.get("OutputFormat", ""), kwargs.get("SampleRate", "")
                )
                and kwargs["VoiceId"] == self._properties.voice_id
            )
        except KeyError:
            return False

    def _synthesize(
        self, text: str, handle_embedded_phonemes=False, **kwargs
    ) -> Iterable[bytes]:
        # TODO(rkjaran): This is mostly the same for all (both) local
        #   backends... Refactor.
        if not self._is_valid(**kwargs):
            raise ValueError("Synthesize request not valid")

        for chunk in self._backend.synthesize(
            text,
            emit_speech_marks=kwargs["OutputFormat"] == "json",
            sample_rate=int(kwargs["SampleRate"]),
            handle_embedded_phonemes=handle_embedded_phonemes,
        ):
            if current_app.config["USE_FFMPEG"]:
                if kwargs["OutputFormat"] == "ogg_vorbis":
                    yield ffmpeg.to_ogg_vorbis(
                        chunk,
                        src_sample_rate=kwargs["SampleRate"],
                        sample_rate=kwargs["SampleRate"],
                    )
                elif kwargs["OutputFormat"] == "mp3":
                    yield ffmpeg.to_mp3(
                        chunk,
                        src_sample_rate=kwargs["SampleRate"],
                        sample_rate=kwargs["SampleRate"],
                    )
            if kwargs["OutputFormat"] in ("pcm", "json"):
                yield chunk

    def synthesize(self, text: str, **kwargs) -> Iterable[bytes]:
        """Synthesize audio from a string of characters."""
        return self._synthesize(text, **kwargs)

    def synthesize_from_ssml(self, ssml: str, **kwargs) -> Iterable[bytes]:
        """Synthesize audio from SSML markup."""
        # TODO(rkjaran): Move SSML parser out of here and make it more general
        parser = SSMLParser()
        parser.feed(ssml)
        text = parser.get_fastspeech_string()
        parser.close()
        return self._synthesize(text=text, handle_embedded_phonemes=True, **kwargs)

    @property
    def properties(self) -> VoiceProperties:
        return self._properties


_OGG_VORBIS_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_MP3_SAMPLE_RATES = ["8000", "16000", "22050", "24000"]
_PCM_SAMPLE_RATES = ["8000", "16000", "22050"]
SUPPORTED_OUTPUT_FORMATS = [
    OutputFormat(output_format="pcm", supported_sample_rates=_PCM_SAMPLE_RATES),
    OutputFormat(
        output_format="ogg_vorbis", supported_sample_rates=_OGG_VORBIS_SAMPLE_RATES
    ),
    OutputFormat(output_format="mp3", supported_sample_rates=_MP3_SAMPLE_RATES),
    OutputFormat(output_format="json", supported_sample_rates=[]),
]


def _is_output_format_supported(output_format: str, sample_rate: str) -> bool:
    return any((output_format, sample_rate) == fmt for fmt in SUPPORTED_OUTPUT_FORMATS)
