from pathlib import Path

from ..grapheme_to_phoneme import SequiturGraphemeToPhonemeTranslator

def phoneseq_to_str(seq: "list[str]"):
    return "".join(seq)

class TestSequiturGraphemeToPhonemeTranslator:
    _model_path: Path
    _language_code: str
    _t: SequiturGraphemeToPhonemeTranslator

    def __init__(
        self,
        model_path = Path("external/sequitur_model/file/sequitur.mdl"),
        language_code = "is-IS",
    ) -> None:
        self._model_path = model_path
        self._language_code = language_code
        self._t = SequiturGraphemeToPhonemeTranslator(
            lang_model_paths={ 
                self._language_code: self._model_path
            }
        )

    def translate_to_str(self, text: str):
        return phoneseq_to_str(self._t.translate(text, self._language_code))

    def test_two_multiword_01(self):
        text: str = "Halló heimur"
        assert self.translate_to_str(text) == "halouheiːmʏr"