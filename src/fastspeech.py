import os
import sys
import io
import wave
from typing import BinaryIO
import torch
import numpy as np
from flask import current_app

sys.path.insert(0, "src/lib/fastspeech")
from lib.fastspeech.synthesize import synthesize, preprocess, get_FastSpeech2, load_g2p
from lib.fastspeech import utils
from scipy.io import wavfile
import hparams as hp
from phonemes import XSAMPA_IPA_MAP, IPA_XSAMPA_MAP


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
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.melgan_model = utils.get_melgan(full_path=melgan_vocoder_path)
        self.melgan_model.to(self.device)
        self.fs_model = get_FastSpeech2(490000, full_path=fastspeech_model_path)
        self.fs_model.to(self.device)
        self.g2p_model = load_g2p(sequitur_model_path)

    def synthesize(self, text_string: str, filename: BinaryIO) -> None:
        """Surround phoneme strings with {}"""
        duration_control = 1.0
        pitch_control = 1.0
        energy_control = 1.0
        text = preprocess(text_string, self.g2p_model)
        src_len = torch.from_numpy(np.array([text.shape[1]])).to(self.device)
        (
            mel,
            mel_postnet,
            log_duration_output,
            f0_output,
            energy_output,
            _,
            _,
            mel_len,
        ) = self.fs_model(
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
            wav = self.melgan_model.inference(mel_postnet_torch).cpu().numpy()
        wav = wav.astype("int16")
        wavfile.write(filename, hp.sampling_rate, wav)
