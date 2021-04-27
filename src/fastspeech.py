import os
import sys
import io
import wave
from typing import BinaryIO
import torch
import numpy as np

sys.path.insert(0, "src/lib/fastspeech")
from lib.fastspeech.synthesize import synthesize, preprocess, get_FastSpeech2, load_g2p
from lib.fastspeech import utils
from scipy.io import wavfile
import hparams as hp

IPA_XSAMPA_MAP = {
    "a": "a",
    "ai": "ai",
    "aiː": "ai:",
    "au": "au",
    "auː": "au:",
    "aː": "a:",
    "c": "c",
    "cʰ": "c_h",
    "ei": "ei",
    "eiː": "ei:",
    "f": "f",
    "h": "h",
    "i": "i",
    "iː": "i:",
    "j": "j",
    "k": "k",
    "kʰ": "k_h",
    "l": "l",
    "l̥": "l_0",
    "m": "m",
    "m̥": "m_0",
    "n": "n",
    "n̥": "n_0",
    "ou": "ou",
    "ouː": "ou:",
    "p": "p",
    "pʰ": "p_h",
    "r": "r",
    "r̥": "r_0",
    "s": "s",
    "t": "t",
    "tʰ": "t_h",
    "u": "u",
    "uː": "u:",
    "v": "v",
    "x": "x",
    "ç": "C",
    "ð": "D",
    "ŋ": "N",
    "ŋ̊": "N_0",
    "œ": "9",
    "œy": "9Y",
    "œyː": "9Y:",
    "œː": "9:",
    "ɔ": "O",
    "ɔi": "Oi",
    "ɔː": "O:",
    "ɛ": "E",
    "ɛː": "E:",
    "ɣ": "G",
    "ɪ": "I",
    "ɪː": "I:",
    "ɲ": "J",
    "ɲ̊": "J_0",
    "ʏ": "Y",
    "ʏi": "Yi",
    "ʏː": "Y:",
    "θ": "T",
}

XSAMPA_IPA_MAP = {val: key for key, val in IPA_XSAMPA_MAP.items()}

MELGAN_VOCODER_PATH = os.environ.get(
    "MELGAN_VOCODER_PATH", "lib/fastspeech/v2021-01-01/vocoder_aca5990_3350.pt"
)
FASTSPEECH_MODEL_PATH = os.environ.get(
    "FASTSPEECH_MODEL_PATH", "lib/fastspeech/v2021-01-01/checkpoint_490000.pth.tar"
)
SEQUITUR_MODEL_PATH = os.environ.get(
    "SEQUITUR_MODEL_PATH", "lib/fastspeech/models/is-IS.ipd_clean_slt2018.mdl"
)


class FastSpeech2Synthesizer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.melgan_model = utils.get_melgan(full_path=MELGAN_VOCODER_PATH)
        self.melgan_model.to(self.device)
        self.fs_model = get_FastSpeech2(490000, full_path=FASTSPEECH_MODEL_PATH)
        self.fs_model.to(self.device)
        self.g2p_model = load_g2p(SEQUITUR_MODEL_PATH)

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
