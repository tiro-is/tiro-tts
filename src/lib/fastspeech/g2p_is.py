from optparse import Values
import SequiturTool
from sequitur import Translator
from align_phonemes import Aligner


def load_g2p(model_path):
    sequitur_options = Values()
    sequitur_options.modelFile = model_path
    sequitur_options.resume_from_checkpoint = False
    sequitur_options.shouldRampUp = False
    sequitur_options.trainSample = False
    sequitur_options.shouldTranspose = False
    sequitur_options.shouldSelfTest = False
    sequitur_options.newModelFile = False
    model = SequiturTool.procureModel(sequitur_options, None)
    if not model:
        print('Can\'t load g2p model.')
        sys.exit(1)
    return model


def translate(text, g2p_model):
    text = text.replace(",", " ,")
    text = text.replace(".", " .")

    translator = Translator(g2p_model)
    phone = []
    phoneme_str_open = False
    for w in text.split(" "):
        try:
            if phoneme_str_open:
                if w.endswith("}"):
                    phone.append(w.replace("}", ""))
                    phoneme_str_open = False
                else:
                    phone.append(w)
            elif not phoneme_str_open:
                print(w)
                if w.startswith("{") and w.endswith("}"):
                    print(Aligner().align(
                        w.replace("{", "").replace("}", "")).split(" "))
                    phone.extend(Aligner().align(
                        w.replace("{", "").replace("}", "")).split(" "))
                elif w.startswith("{"):
                    phone.append(w.replace("{", ""))
                    phoneme_str_open = True
                elif w in [".", ","]:
                    phone.append("sp")
                else:
                    phones = translator(w.lower())
                    phone.extend(phones)
            phone.append(" ")
        except Translator.TranslationFailure:
            pass
    return phone


if __name__ == "__main__":
    t = translate("halló, þetta er á íslensku")
    print(t)

