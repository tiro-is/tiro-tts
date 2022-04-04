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
from typing import Callable, Dict, Iterable, List, Literal, NewType, Optional, Union

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
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        """Translate a graphemic text into a string of phones

        Args:
            text: Freeform text to be converted to graphemes

            lang: BCP-47 language code to use

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
        for idx, word in enumerate(words):
            if word != WORD_SENTENCE_SEPARATOR:
                # TODO(rkjaran): Cover more punctuation (Unicode)
                punctuation = re.sub(r"[{}\[\]]", "", string.punctuation)
                g2p_word = re.sub(r"([{}])".format(punctuation), r" \1 ", word.symbol)
                word.phone_sequence = self.translate(g2p_word, lang, alphabet=alphabet)
            yield word
            if word.is_spoken() and alphabet == "x-sampa+syll+stress":
                yield Word(phone_sequence=["."])


class EmbeddedPhonemeTranslatorBase(GraphemeToPhonemeTranslatorBase):
    @abstractmethod
    def _translate(self, w: str, lang: LangID, alphabet: Alphabet = "ipa"):
        ...

    def translate(
        self,
        text: str,
        lang: LangID,
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        text = text.replace(",", " ,")
        text = text.replace(".", " .")

        def translate_fn(w: str) -> PhoneSeq:
            return self._translate(w, lang, alphabet=alphabet)

        return self._process_embedded(text, translate_fn, alphabet)

    def _process_embedded(
        self, text: str, translate_fn: Callable[[str], PhoneSeq], alphabet: Alphabet
    ) -> PhoneSeq:
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
                    phone.append(
                        "." if alphabet == "x-sampa+syll+stress" else SHORT_PAUSE
                    )
                else:
                    phones = translate_fn(w)
                    phone.extend(phones)

        return phone


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
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        phone = []
        for t in self._translators:
            phone = t.translate(text, lang, alphabet=alphabet)
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


class LexiconGraphemeToPhonemeTranslator(EmbeddedPhonemeTranslatorBase):
    _lookup_lexicon: Dict[LangID, LexiconBase]
    _language_code: LangID
    _alphabet: Alphabet

    def __init__(
        self,
        lexicon: Union[LexiconBase, Path],
        language_code: LangID,
        alphabet: Alphabet,
    ):
        if isinstance(lexicon, Path):
            self._lookup_lexicon = SimpleInMemoryLexicon(lexicon, alphabet)
        else:
            self._lookup_lexicon = lexicon
        self._language_code = language_code

        # TODO(rkjaran): By default LexiconBase.get(...) returns IPA, change this once
        #   we add a parameter for the alphabet to .get()
        self._alphabet = "ipa"

    def _translate(
        self,
        w: str,
        lang: LangID,
        alphabet: Alphabet = "ipa",
    ):
        phones: PhoneSeq = []
        w_lower = w.lower()
        lexicon = self._lookup_lexicon
        if lexicon:
            phones = lexicon.get(w, [])
            if not phones:
                phones = lexicon.get(w_lower, [])
        # TODO(rkjaran): By default LexiconBase.get(...) returns IPA, change this once
        #   we add a parameter for the alphabet to .get()
        if alphabet != "ipa":
            phones = convert_ipa_to_xsampa(phones)
            if alphabet == "x-sampa+syll+stress":
                phones = convert_xsampa_to_xsampa_with_stress(phones, w)

        return phones


class SequiturGraphemeToPhonemeTranslator(EmbeddedPhonemeTranslatorBase):
    # TODO(rkjaran): Implement a DB backed version of this
    _lang_models: Dict[str, sequitur.ModelTemplate]
    _language_code: LangID
    _alphabet: Alphabet

    def __init__(
        self,
        lang_model_path: Path,
        language_code: LangID,
        alphabet: Alphabet,
    ):
        self._lang_model = g2p.SequiturTool.procureModel(
            SequiturOptions(modelFile=str(lang_model_path)), g2p.loadG2PSample
        )
        self._language_code = language_code
        self._alphabet = alphabet

    def _translate(
        self,
        w: str,
        lang: LangID,
        alphabet: Alphabet = "ipa",
    ) -> PhoneSeq:
        translator = g2p.Translator(self._lang_model)
        phones: PhoneSeq = []
        w_lower = w.lower()
        if not phones:
            try:
                phones = translator(w_lower)
            except g2p.Translator.TranslationFailure:
                pass
        if self._alphabet == "ipa" and alphabet in (
            "x-sampa",
            "x-sampa+syll+stress",
        ):
            phones = convert_ipa_to_xsampa(phones)

        if self._alphabet in ("ipa", "x-sampa") and alphabet == "x-sampa+syll+stress":
            phones = convert_xsampa_to_xsampa_with_stress(phones, w)

        return phones


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
