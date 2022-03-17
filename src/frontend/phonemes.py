# Copyright 2021-2022 Tiro ehf.
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
from typing import List, Literal

PhoneSeq = List[str]
Alphabet = Literal["x-sampa", "ipa", "x-sampa+syll+stress"]

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

DEFAULT_PHONEMES = XSAMPA_IPA_MAP.keys()

XSAMPA_VOWELS = {
    "a",
    "ai",
    "ai:",
    "au",
    "au:",
    "a:",
    "ei",
    "ei:",
    "i",
    "i:",
    "ou",
    "ou:",
    "u",
    "u:",
    "9",
    "9i",
    "9i:",
    "9:",
    "O",
    "Oi",
    "O:",
    "E",
    "E:",
    "G",
    "I",
    "I:",
    "Y",
    "Yi",
    "Y:",
}

XSAMPA_VOWELS_AND_STRESS = set(
    [ph + "0" for ph in XSAMPA_VOWELS] + [ph + "1" for ph in XSAMPA_VOWELS]
)


class Aligner:
    def __init__(self, phoneme_set=None, align_sep=" ", cleanup=""):
        "Align according to phoneme_set"
        if phoneme_set:
            self.phoneme_set = phoneme_set
        else:
            self.phoneme_set = DEFAULT_PHONEMES
        self.phoneme_stats = dict(
            zip(self.phoneme_set, [0 for i in range(len(self.phoneme_set))])
        )
        self.max_plen = 0
        self.align_sep = align_sep
        self.clean_trtbl = str.maketrans("", "", cleanup)
        for phoneme in self.phoneme_set:
            plen = len(phoneme)
            self.max_plen = plen if plen > self.max_plen else self.max_plen

    def find_longest(self, partial_pstring, phoneme_string):
        if len(partial_pstring) < self.max_plen:
            max_len = len(partial_pstring)
        else:
            max_len = self.max_plen

        r = range(1, max_len + 1)[::-1]

        for l in r:
            if partial_pstring[0:l] in self.phoneme_set:
                self.phoneme_stats[partial_pstring[0:l]] += 1
                return l
        raise ValueError(
            'Invalid symbol found in "{}"'.format(
                phoneme_string + "\t" + partial_pstring[0:l]
            )
        )

    def align(self, phoneme_string):
        phoneme_string = self.clean(phoneme_string)
        sublengths = []
        w = phoneme_string
        while len(w) > 0:
            offset = self.find_longest(w, phoneme_string)
            w = w[offset:]
            sublengths.append(offset)
        aligned = []
        a = 0
        for b in sublengths:
            aligned.append(phoneme_string[a : a + b])
            a = a + b
        return self.align_sep.join(aligned)

    def clean(self, phoneme_string):
        """Clean some unwanted characters from string"""
        return phoneme_string.translate(self.clean_trtbl)

    @staticmethod
    def read_file_as_set(fpath):
        phonemes = set()
        with open(fpath) as fobj:
            for line in fobj:
                line = line.strip()
                if line[0] != "#":
                    phonemes.add(line)
        return phonemes


ALIGNER_IPA = Aligner(phoneme_set=set(IPA_XSAMPA_MAP.keys()))
ALIGNER_XSAMPA = Aligner(phoneme_set=set(XSAMPA_IPA_MAP.keys()))


def convert_ipa_to_xsampa(phoneme: PhoneSeq) -> PhoneSeq:
    return [IPA_XSAMPA_MAP[ph] for ph in phoneme]


def convert_xsampa_to_ipa(phoneme: PhoneSeq) -> PhoneSeq:
    return [XSAMPA_IPA_MAP[ph] for ph in phoneme]


def convert_xsampa_to_xsampa_with_stress(phoneme: PhoneSeq) -> PhoneSeq:
    return [ph + "0" if ph in XSAMPA_VOWELS else ph for ph in phoneme]


def align_ipa_from_xsampa(phoneme_string: str) -> str:
    return " ".join(
        XSAMPA_IPA_MAP[phn]
        for phn in ALIGNER_XSAMPA.align(phoneme_string.replace(" ", "")).split(" ")
    )


def _align_ipa(phoneme_string: str):
    return " ".join(
        phn for phn in ALIGNER_IPA.align(phoneme_string.replace(" ", "")).split(" ")
    )
