from pathlib import Path

from ..grapheme_to_phoneme import SequiturGraphemeToPhonemeTranslator

def phoneseq_to_str(seq: "list[str]"):
    return "".join(seq)

class TestSequiturGraphemeToPhonemeTranslator:
    _model_path: Path = Path("external/sequitur_model/file/sequitur.mdl")
    _language_code: str = "is-IS"
    _t: SequiturGraphemeToPhonemeTranslator = SequiturGraphemeToPhonemeTranslator(
        lang_model_paths={ 
            _language_code: _model_path
        }
    )

    def translate_to_str(self, text: str):
        return phoneseq_to_str(self._t.translate(text, self._language_code))

    def test_two_multiword_01(self):
        text: str = "Halló heimur"
        assert self.translate_to_str(text) == "halouheiːmʏr"