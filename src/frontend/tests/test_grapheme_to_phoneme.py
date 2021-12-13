from pathlib import Path

from ..grapheme_to_phoneme import SequiturGraphemeToPhonemeTranslator

def phoneseq_to_str(seq: "list[str]"):
    return "".join(seq)

class TestSequiturGraphemeToPhonemeTranslator:
    def test_one_halló(self):
        language_code: str = "is-IS"
        model_path: str = Path("external/sequitur_model/file/sequitur.mdl")
        text: str = "Halló heimur"

        t = SequiturGraphemeToPhonemeTranslator(
            lang_model_paths={ 
                language_code: model_path
            }
        )

        assert phoneseq_to_str(t.translate(text, language_code)) == "halouheiːmʏr"