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
import os
import sys
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lib/fastspeech"))
from src.lib.fastspeech.align_phonemes import Aligner

PhoneSeq = List[str]

SHORT_PAUSE = "sp"

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
    "œy": "9i",
    "œyː": "9i:",
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
    SHORT_PAUSE: SHORT_PAUSE,
}

XSAMPA_IPA_MAP = {val: key for key, val in IPA_XSAMPA_MAP.items()}

ALIGNER_IPA = Aligner(phoneme_set=set(IPA_XSAMPA_MAP.keys()))
ALIGNER_XSAMPA = Aligner(phoneme_set=set(XSAMPA_IPA_MAP.keys()))


def convert_ipa_to_xsampa(phoneme: PhoneSeq) -> PhoneSeq:
    return [IPA_XSAMPA_MAP[ph] for ph in phoneme]


def convert_xsampa_to_ipa(phoneme: PhoneSeq) -> PhoneSeq:
    return [XSAMPA_IPA_MAP[ph] for ph in phoneme]


def align_ipa_from_xsampa(phoneme_string: str) -> str:
    return " ".join(
        XSAMPA_IPA_MAP[phn]
        for phn in ALIGNER_XSAMPA.align(phoneme_string.replace(" ", "")).split(" ")
    )


def _align_ipa(phoneme_string: str):
    return " ".join(
        phn for phn in ALIGNER_IPA.align(phoneme_string.replace(" ", "")).split(" ")
    )
