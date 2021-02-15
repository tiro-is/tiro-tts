from optparse import Values
import SequiturTool
from sequitur import Translator


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
    for w in text.split(" "):
        try:
            if w in [".", ","]:
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

