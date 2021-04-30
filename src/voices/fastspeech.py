import os
import sys
import io
import wave
import typing
from typing import BinaryIO
import torch
import numpy as np
from flask import current_app
from html.parser import HTMLParser
from . import VoiceBase, VoiceProperties, OutputFormat

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lib/fastspeech"))
from lib.fastspeech.synthesize import synthesize, preprocess, get_FastSpeech2, load_g2p
from lib.fastspeech import utils
from lib.fastspeech.align_phonemes import Aligner
from scipy.io import wavfile
import hparams as hp
from .phonemes import XSAMPA_IPA_MAP, IPA_XSAMPA_MAP


def _align_ipa_from_xsampa(phoneme_string: str):
    return " ".join(
        XSAMPA_IPA_MAP[phn]
        for phn in Aligner(phoneme_set=set(XSAMPA_IPA_MAP.keys()))
        .align(phoneme_string.replace(" ", ""))
        .split(" ")
    )


def _align_ipa(phoneme_string: str):
    return " ".join(
        phn
        for phn in Aligner(phoneme_set=set(IPA_XSAMPA_MAP.keys()))
        .align(phoneme_string.replace(" ", ""))
        .split(" ")
    )


class SSMLParser(HTMLParser):
    _ALLOWED_TAGS = ["speak", "phoneme"]
    _first_tag_seen: bool
    _tags_queue: typing.List[str]
    _prepared_fastspeech_strings: typing.List[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._first_tag_seen = False
        self._tags_queue = []
        self._prepared_fastspeech_strings = []

    def handle_starttag(self, tag, attrs):
        print("Encountered a start tag:", tag)
        if tag not in SSMLParser._ALLOWED_TAGS:
            raise ValueError("Unsupported tag encountered: {}".format(tag))
        if not self._first_tag_seen:
            if tag != "speak":
                raise ValueError("Start tag is not <speak>")
            self._first_tag_seen = True

        if tag == "phoneme":
            attrs_map = dict(attrs)
            if attrs_map.get("alphabet") != "x-sampa" or "ph" not in attrs_map:
                raise ValueError(
                    "<phoneme> tag has to have 'alphabet' and 'ph' attributes"
                )
            self._prepared_fastspeech_strings.append(
                "{%s}" % _align_ipa_from_xsampa(attrs_map["ph"])
            )
        self._tags_queue.append(tag)

    def handle_endtag(self, tag):
        print("Encountered an end tag :", tag)
        self._tags_queue.pop()

    def handle_data(self, data):
        if self._tags_queue[-1] != "phoneme":
            self._prepared_fastspeech_strings.append(data.strip())
        print("Encountered some data  :", data)

    def get_fastspeech_string(self):
        return " ".join(self._prepared_fastspeech_strings)


MELGAN_VOCODER_PATH = current_app.config["MELGAN_VOCODER_PATH"]
FASTSPEECH_MODEL_PATH = current_app.config["FASTSPEECH_MODEL_PATH"]
SEQUITUR_MODEL_PATH = current_app.config["SEQUITUR_MODEL_PATH"]


class FastSpeech2Synthesizer:
    def __init__(
        self,
        melgan_vocoder_path: str = MELGAN_VOCODER_PATH,
        fastspeech_model_path: str = FASTSPEECH_MODEL_PATH,
        sequitur_model_path: str = SEQUITUR_MODEL_PATH,
    ):
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._melgan_model = utils.get_melgan(full_path=melgan_vocoder_path)
        self._melgan_model.to(self._device)
        self._fs_model = get_FastSpeech2(490000, full_path=fastspeech_model_path)
        self._fs_model.to(self._device)
        self._g2p_model = load_g2p(sequitur_model_path)

    def synthesize(self, text_string: str, filename: BinaryIO) -> None:
        """Surround phoneme strings with {}"""
        duration_control = 1.0
        pitch_control = 1.0
        energy_control = 1.0
        text = preprocess(text_string, self._g2p_model)
        src_len = torch.from_numpy(np.array([text.shape[1]])).to(self._device)
        (
            mel,
            mel_postnet,
            log_duration_output,
            f0_output,
            energy_output,
            _,
            _,
            mel_len,
        ) = self._fs_model(
            text,
            src_len,
            d_control=duration_control,
            p_control=pitch_control,
            e_control=energy_control,
        )

        mel_postnet_torch = mel_postnet.transpose(1, 2).detach()
        mel = mel[0].cpu().transpose(0, 1).detach()
        mel_postnet = mel_postnet[0].cpu().transpose(0, 1).detach()
        f0_output = f0_output[0].detach().cpu().numpy()
        energy_output = energy_output[0].detach().cpu().numpy()

        with torch.no_grad():
            wav = self._melgan_model.inference(mel_postnet_torch).cpu().numpy()
        wav = wav.astype("int16")
        wavfile.write(filename, hp.sampling_rate, wav)


class FastSpeech2Voice(VoiceBase):
    _backend: FastSpeech2Synthesizer
    _properties: VoiceProperties

    def __init__(self, properties: VoiceProperties, backend=FastSpeech2Synthesizer()):
        """Initialize a fixed voice with a FastSpeech2 backend"""
        self._backend = backend
        self._properties = properties

    def _is_valid(self, **kwargs) -> bool:
        # Some sanity checks
        try:
            return (
                kwargs["OutputFormat"] == "pcm"
                and kwargs["SampleRate"] == "22050"
                and kwargs["VoiceId"] == self._properties.voice_id
                and "Text" in kwargs
            )
        except KeyError:
            return False

    def synthesize(self, text: str, **kwargs) -> bytes:
        # TODO(rkjaran): chunk the content
        if not self._is_valid(**kwargs):
            raise ValueError("Synthesize request not valid")

        content = io.BytesIO()
        self._backend.synthesize(text, content)
        return content

    def synthesize_from_ssml(self, ssml: str, **kwargs) -> bytes:
        parser = SSMLParser()
        parser.feed(ssml)
        text = parser.get_fastspeech_string()
        parser.close()
        return self.synthesize(text=text, **kwargs)

    @property
    def properties(self) -> VoiceProperties:
        return self._properties


_PCM_SAMPLE_RATES = ["22050"]
_SUPPORTED_OUTPUT_FORMATS = [
    OutputFormat(output_format="pcm", supported_sample_rates=_PCM_SAMPLE_RATES),
]

# List of all available fastspeech voices
VOICES = [
    VoiceProperties(
        voice_id="Other",
        name="Other",
        gender="Male",
        language_code="is-IS",
        language_name="Íslenska",
        supported_output_formats=_SUPPORTED_OUTPUT_FORMATS,
    )
]
