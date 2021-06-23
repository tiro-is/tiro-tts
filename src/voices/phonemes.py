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
import re
from abc import ABC
from pathlib import Path
from typing import Dict, List, Literal, NewType, Optional, Iterable

import g2p  # from sequitur
import sequitur

from lib.fastspeech.align_phonemes import Aligner

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


PhoneSeq = List[str]
LangID = NewType("LangID", str)


class GraphemeToPhonemeTranslatorBase(ABC):
    def translate(
        self, text: str, lang: LangID, failure_langs: Optional[Iterable[LangID]] = None
    ) -> PhoneSeq:
        """Translate a graphemic text into a string of phones

        Args:
            text: Freeform text to be converted to graphemes

            lang: BCP-47 language code to use

            failure_langs: Languages to us as "backoff" when translation (and perhaps
                lookup) fails for the primary language

        Returns:
            A list of strings, where each string is a phone from a defined set of
            phones.

        """
        return NotImplemented


class SequiturOptions(dict):
    """
    Wrapper class for Sequitur options
    """

    def __init__(
        self,
        modelFile: str = "final.mdl",
        variants_number: int = 4,
        variants_mass: float = 0.9,
    ):
        super(SequiturOptions, self).__init__(
            modelFile=modelFile,
            encoding="UTF-8",
            variants_number=variants_number,
            variants_mass=variants_mass,
        )

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value


class SequiturGraphemeToPhonemeTranslator(GraphemeToPhonemeTranslatorBase):
    # TODO(rkjaran): Implement a DB backed version of this
    _lang_models: Dict[str, sequitur.ModelTemplate]
    _lookup_lexica: Dict[LangID, Dict[str, PhoneSeq]]

    def __init__(
        self,
        lang_model_paths: Dict[LangID, Path],
        lexicon_paths: Optional[Dict[LangID, Path]] = None,
    ):
        self._lang_models = {
            lang: g2p.SequiturTool.procureModel(
                SequiturOptions(modelFile=str(path)), g2p.loadG2PSample
            )
            for lang, path in lang_model_paths.items()
        }

        if not lexicon_paths:
            lexicon_paths = {}

        # TODO(rkjaran): Validate phone set
        self._lookup_lexica = {
            lang: self._read_lexicon(path) for lang, path in lexicon_paths.items()
        }

    @staticmethod
    def _read_lexicon(lex_path: Path) -> Dict[str, PhoneSeq]:
        """Read a Kaldi style lexicon."""
        # TODO(rkjaran): Support pronunciation variants, possibly with POS info
        lexicon: Dict[str, PhoneSeq] = dict()
        lex_has_probs = None
        with lex_path.open() as lex_f:
            for line in lex_f:
                fields = line.strip().split()
                # Probe first line for syntax
                if lex_has_probs is None:
                    lex_has_probs = re.match(r"[0-1]\.[0-9]+", fields[1]) is not None
                word = fields[0]
                if lex_has_probs:
                    pron = fields[2:]
                else:
                    pron = fields[1:]
                lexicon[word] = pron
        return lexicon

    def translate(
        self, text: str, lang: LangID, failure_langs: Optional[Iterable[LangID]] = None
    ) -> PhoneSeq:
        # TODO(rkjaran): Currently, this has special handling for phoneme strings
        #                embedded with enclosing curly brackets {}. This should be
        #                handled at a higher level.
        translator = g2p.Translator(self._lang_models[lang])
        fail_translators = [
            {
                "lang": lang_,
                "translator": g2p.Translator(self._lang_models[lang_]),
            }
            for lang_ in (failure_langs or [])
        ]

        text = text.replace(",", " ,")
        text = text.replace(".", " .")

        phone = []
        phoneme_str_open = False
        aligner = Aligner()
        for w in text.split(" "):
            if phoneme_str_open:
                if w.endswith("}"):
                    phone.append(w.replace("}", ""))
                    phoneme_str_open = False
                else:
                    phone.append(w)
            elif not phoneme_str_open:
                if w.startswith("{") and w.endswith("}"):
                    phone.extend(
                        aligner.align(w.replace("{", "").replace("}", "")).split(" ")
                    )
                elif w.startswith("{"):
                    phone.append(w.replace("{", ""))
                    phoneme_str_open = True
                elif w in [".", ","]:
                    phone.append("sp")
                else:
                    w_lower = w.lower()
                    phones = self._lookup_lexica.get(lang, {}).get(w, [])
                    if not phones:
                        phones = self._lookup_lexica.get(lang, {}).get(w_lower, [])
                    if not phones:
                        try:
                            phones = translator(w_lower)
                        except g2p.Translator.TranslationFailure:
                            for t in fail_translators:
                                try:
                                    phones = self._lookup_lexica.get(t["lang"], {}).get(
                                        w, []
                                    )
                                    if not phones:
                                        phones = self._lookup_lexica.get(
                                            t["lang"], {}
                                        ).get(w_lower, [])
                                    if not phones:
                                        phones = t["translator"](w_lower)
                                    if phones:
                                        break
                                except g2p.Translator.TranslationFailure:
                                    continue
                    phone.extend(phones)
        return phone
