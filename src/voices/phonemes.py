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
from typing import List

PhoneSeq = List[str]

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


def convert_ipa_to_xsampa(phoneme: PhoneSeq) -> PhoneSeq:
    return [IPA_XSAMPA_MAP[ph] for ph in phoneme]


def convert_xsampa_to_ipa(phoneme: PhoneSeq) -> PhoneSeq:
    return [XSAMPA_IPA_MAP[ph] for ph in phoneme]
