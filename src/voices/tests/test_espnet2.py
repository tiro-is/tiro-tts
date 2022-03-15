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
from pathlib import Path

import pytest

from src.frontend.grapheme_to_phoneme import IceG2PTranslator
from src.frontend.normalization import BasicNormalizer
from src.voices.espnet2 import Espnet2Synthesizer


class TestEspnet2Backend:
    model_uri = "file://external/test_models/dilja/espnet2.zip"
    vocoder_uri = "file://external/test_models/universal/pwg.zip"
    normalizer = BasicNormalizer()
    phonetizer = IceG2PTranslator()
    backend = Espnet2Synthesizer(
        model_uri, vocoder_uri, phonetizer, normalizer, alphabet="x-sampa+syll+stress"
    )

    def test_synthesize_basic_text(self):
        text = "Hæ hæ, hver ert þú?"
        chunks = list(self.backend.synthesize(text, sample_rate=22050))
        assert len(chunks) > 0

    def test_synthesize_empt_text(self):
        text = ""
        chunks = list(self.backend.synthesize(text, sample_rate=22050))
        assert len(chunks) == 0

    def test_synthesize_nonnative_sample_rate(self):
        text = "Hehe hvað heiti ég?"
        chunks = list(self.backend.synthesize(text, sample_rate=8000))
        assert len(chunks) > 0
