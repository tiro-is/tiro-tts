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
from pathlib import Path
from typing import Dict, NewType

from .phonemes import PhoneSeq

LangID = NewType("LangID", str)


def read_kaldi_lexicon(lex_path: Path) -> Dict[str, PhoneSeq]:
    """Read a Kaldi style lexicon."""
    # TODO(rkjaran): Support pronunciation variants, possibly with POS info
    lexicon: Dict[str, PhoneSeq] = dict()
    lex_has_probs = None
    with lex_path.open() as lex_f:
        for line in lex_f:
            fields = line.strip().split()
            # Probe first line for syntax
            if lex_has_probs is None:
                lex_has_probs = re.match(
                    r"[0-1]\.[0-9]+", fields[1]) is not None
            word = fields[0]
            if lex_has_probs:
                pron = fields[2:]
            else:
                pron = fields[1:]
            lexicon[word] = pron
    return lexicon
