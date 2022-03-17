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
import re
import string
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Literal, NewType, Optional

import g2p  # from sequitur
import ice_g2p.transcriber
import sequitur

from .lexicon import LangID, LexiconBase, SimpleInMemoryLexicon, read_kaldi_lexicon
from .phonemes import (
    SHORT_PAUSE,
    Aligner,
    Alphabet,
    PhoneSeq,
    convert_ipa_to_xsampa,
    convert_xsampa_to_ipa,
    convert_xsampa_to_xsampa_with_stress,
)
from .words import WORD_SENTENCE_SEPARATOR, Word


class GraphemeToPhonemeTranslatorBase(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        lang: LangID,
        failure_langs: Optional[Iterable[LangID]] = None,
        alphabet: Alphabet = "ipa",
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
        ...

    def translate_words(
        self,
        words: Iterable[Word],
        lang: LangID,
        alphabet: Alphabet = "ipa",
    ) -> Iterable[Word]:
        # TODO(rkjaran): Syllabification in IceG2PTranslator does not work well with
        #   single word inputs. Need to figure out an interface that includes the
        #   necessary context.
        for word in words:
            if not word == WORD_SENTENCE_SEPARATOR:
                # TODO(rkjaran): Cover more punctuation (Unicode)
                punctuation = re.sub(r"[{}\[\]]", "", string.punctuation)
                g2p_word = re.sub(r"([{}])".format(punctuation), r" \1 ", word.symbol)
                # TODO(rkjaran): The language code shouldn't be hardcoded here. Should
                #                it be here at all?
                word.phone_sequence = self.translate(g2p_word, lang, alphabet=alphabet)
            yield word


class ComposedTranslator(GraphemeToPhonemeTranslatorBase):
    """ComposedTranslator

    Group together one or more translators which are used in sequence until the text is
    successfully translated (or we run out of translators).

    Example:
      >>> ComposedTranslator(LexiconGraphemeToPhonemeTranslator(...), SequiturGraphemeToPhonemeTranslator(...))
    """

    _translators: List[GraphemeToPhonemeTranslatorBase]

    def __init__(self, *translators):
        if len(translators) < 1:
            raise ValueError("Needs at least 1 argument.")
        self._translators = list(translators)

    def translate(
        self,
        text: str,
        lang: LangID,
        failure_langs: Optional[Iterable[LangID]] = None,
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        phone = []
        for t in self._translators:
            phone = t.translate(text, lang, failure_langs, alphabet=alphabet)
            if phone:
                break
        return phone


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


class LexiconGraphemeToPhonemeTranslator(GraphemeToPhonemeTranslatorBase):
    _lookup_lexica: Dict[LangID, LexiconBase]

    def __init__(self, lexica: Dict[LangID, LexiconBase]):
        self._lookup_lexica = lexica

        for lang, lex in lexica.items():
            if isinstance(lex, Path):
                self._lookup_lexica[lang] = SimpleInMemoryLexicon(lex, "x-sampa")

    def translate(
        self,
        text: str,
        lang: LangID,
        failure_langs: Optional[Iterable[LangID]] = None,
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        if not failure_langs:
            failure_langs = []
        # TODO(rkjaran): Currently, this has special handling for phoneme strings
        #                embedded with enclosing curly brackets {}. This should be
        #                handled at a higher level.  Even more annoyingly it is
        #                replicated in Lexicon* and Sequitur*
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
                    phone.append(SHORT_PAUSE)
                else:
                    phones: PhoneSeq = []
                    w_lower = w.lower()
                    lexicon = self._lookup_lexica.get(lang)
                    if lexicon:
                        phones = lexicon.get(w, [])
                        if not phones:
                            phones = lexicon.get(w_lower, [])
                    if not phones:
                        for lang in failure_langs:
                            fail_lexicon = self._lookup_lexica.get(lang)
                            if fail_lexicon:
                                phones = fail_lexicon.get(w, [])
                                if not phones:
                                    phones = fail_lexicon.get(w_lower, [])
                            if phones:
                                break
                    phone.extend(phones)

        # TODO(rkjaran): By default LexiconBase.get(...) returns IPA, change this once
        #   we add a parameter for the alphabet to .get()
        if alphabet != "ipa":
            phone = convert_ipa_to_xsampa(phone)
            if alphabet == "x-sampa+syll+stress":
                phone = convert_xsampa_to_xsampa_with_stress(phone)
        return phone


class SequiturGraphemeToPhonemeTranslator(GraphemeToPhonemeTranslatorBase):
    # TODO(rkjaran): Implement a DB backed version of this
    _lang_models: Dict[str, sequitur.ModelTemplate]
    _lookup_lexica: Dict[LangID, LexiconBase]

    def __init__(
        self,
        lang_model_paths: Dict[LangID, Path],
        lexica: Optional[Dict[LangID, LexiconBase]] = None,
    ):
        self._lang_models = {
            lang: g2p.SequiturTool.procureModel(
                SequiturOptions(modelFile=str(path)), g2p.loadG2PSample
            )
            for lang, path in lang_model_paths.items()
        }

        self._lookup_lexica = lexica if lexica else {}

    def translate(
        self,
        text: str,
        lang: LangID,
        failure_langs: Optional[Iterable[LangID]] = None,
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        if not failure_langs:
            failure_langs = []

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
                    phones: PhoneSeq = []
                    w_lower = w.lower()
                    lexicon = self._lookup_lexica.get(lang)
                    if lexicon:
                        phones = lexicon.get(w, [])
                        if not phones:
                            phones = lexicon.get(w_lower, [])
                    if not phones:
                        try:
                            phones = translator(w_lower)
                        except g2p.Translator.TranslationFailure:
                            for t in fail_translators:
                                try:
                                    fail_lexicon = self._lookup_lexica.get(t["lang"])
                                    if fail_lexicon:
                                        phones = fail_lexicon.get(w, [])
                                        if not phones:
                                            phones = fail_lexicon.get(w_lower, [])
                                    if not phones:
                                        phones = t["translator"](w_lower)
                                    if phones:
                                        break
                                except g2p.Translator.TranslationFailure:
                                    continue
                    phone.extend(phones)
        return phone


class IceG2PTranslator(GraphemeToPhonemeTranslatorBase):
    _transcriber: ice_g2p.transcriber.Transcriber

    def __init__(self):
        self._transcriber = ice_g2p.transcriber.Transcriber(
            use_dict=True, use_syll=True
        )

    def translate(
        self,
        text: str,
        lang: LangID,
        failure_langs: Optional[Iterable[LangID]] = None,
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        punctuation = re.sub(r"[{}\[\]]", "", string.punctuation)
        text = re.sub(r"([{}])".format(punctuation), "", text)

        if text.strip() == "":
            return []

        out = self._transcriber.transcribe(
            text.lower(),
            syllab=True if alphabet == "x-sampa+syll+stress" else False,
            use_dict=True,
        )

        phone_seq = out.split()
        if alphabet == "ipa":
            return convert_xsampa_to_ipa(phone_seq)

        return phone_seq
