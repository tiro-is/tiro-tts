import torch
import torch.nn as nn
import numpy as np
import os
import argparse
import re
from string import punctuation
from g2p_en import G2p

from fastspeech2 import FastSpeech2
from text import text_to_sequence, sequence_to_text
import hparams as hp
import utils
import audio as Audio
from g2p_is import load_g2p, translate as g2p


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def preprocess(text, g2p_model):
    text = text.rstrip(punctuation)
    phone = g2p(text, g2p_model)
    phone = list(filter(lambda p: p != ' ', phone))
    phone = '{' + '}{'.join(phone) + '}'
    phone = re.sub(r'\{[^\w\s]?\}', '{sp}', phone)
    phone = phone.replace('}{', ' ')

    print('|' + phone + '|')
    sequence = np.array(text_to_sequence(phone, hp.text_cleaners))
    sequence = np.stack([sequence])

    return torch.from_numpy(sequence).long().to(device)


def get_FastSpeech2(num, full_path=None):
    if full_path:
        checkpoint_path = full_path
    else:
        checkpoint_path = os.path.join(hp.checkpoint_path, "checkpoint_{}.pth.tar".format(num))
    model = nn.DataParallel(FastSpeech2())
    model.load_state_dict(torch.load(checkpoint_path, map_location=device)['model'])
    model.requires_grad = False
    model.eval()
    return model


def synthesize(model, waveglow, melgan, text, sentence, prefix='', duration_control=1.0, pitch_control=1.0, energy_control=1.0):
    sentence = sentence[:200]  # long filename will result in OS Error

    src_len = torch.from_numpy(np.array([text.shape[1]])).to(device)

    mel, mel_postnet, log_duration_output, f0_output, energy_output, _, _, mel_len = model(
        text, src_len, d_control=duration_control, p_control=pitch_control, e_control=energy_control)

    mel_torch = mel.transpose(1, 2).detach()
    mel_postnet_torch = mel_postnet.transpose(1, 2).detach()
    mel = mel[0].cpu().transpose(0, 1).detach()
    mel_postnet = mel_postnet[0].cpu().transpose(0, 1).detach()
    f0_output = f0_output[0].detach().cpu().numpy()
    energy_output = energy_output[0].detach().cpu().numpy()

    if not os.path.exists(hp.test_path):
        os.makedirs(hp.test_path)

    Audio.tools.inv_mel_spec(mel_postnet, os.path.join(
        hp.test_path, '{}_griffin_lim_{}.wav'.format(prefix, sentence)))

    sentence_id = sentence[:30]
    if waveglow is not None:
        utils.waveglow_infer(mel_postnet_torch, waveglow, os.path.join(
            hp.test_path, '{}_{}_{}.wav'.format(prefix, hp.vocoder, sentence_id)))
    if melgan is not None:
        utils.melgan_infer(mel_postnet_torch, melgan, os.path.join(
            hp.test_path, '{}_{}_{}.wav'.format(prefix, hp.vocoder, sentence_id)))

    #utils.plot_data([(mel_postnet.numpy(), f0_output, energy_output)], [
    #                'Synthesized Spectrogram'], filename=os.path.join(hp.test_path, '{}_{}.png'.format(prefix, sentence_id)))


if __name__ == "__main__":
    # Test
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-fs', type=str)
    parser.add_argument('--model-melgan', type=str)
    parser.add_argument('--model-g2p', type=str)
    parser.add_argument('--step', type=int, default=30000)
    parser.add_argument('--duration_control', type=float, default=1.0)
    parser.add_argument('--pitch_control', type=float, default=1.0)
    parser.add_argument('--energy_control', type=float, default=1.0)
    args = parser.parse_args()

    if not args.model_g2p:
        raise argparse.ArgumentTypeError("G2P model missing")
    
    sentences = [
        "góðan dag ég kann að tala íslensku alveg hnökralaust eða svona næstum því",
        "hlýnun lengir líf fellibylja yfir landi",
        'Eg skal segja þér, kvað hann, hvað eg hefi hugsað. eg ætla að hafa til þings með mér kistur þær tvær, er Aðalsteinn konungur gaf mér, er hvortveggja er full af ensku silfri. Ætla eg að láta bera kisturnar til Lögbergs, þá er þar er fjölmennast; síðan ætla eg að sá silfrinu, og þykir mér undarlegt, ef allir skipta vel sín í milli; ætla eg, að þar myndi vera þá hrundningar, eða pústrar, eða bærist að um síðir, að allur þingheimurinn berðist.',
        "Vigdís Finnbogadóttir var fjórði forseti Íslands og gegndi hún embættinu frá 1980 til 1996. Hún var fyrsta konan i heiminum sem kosin var í lýðræðislegum kosningum til að gegna hlutverki þjóðhöfðingja.",
        "Í gær kvisaðist það út í Ósló að óvenjulíflegt væri á öldurhúsum nágrannasveitarfélaganna Asker og Bærum af þriðjudegi að vera auk þess sem norska ríkisútvarpið NRK greindi frá því að langar biðraðir væru fyrir utan líkamsræktarstöðvar bæja þessara, nokkuð sem íbúar þar höfðu sjaldan upplifað.",
        "Japanski bílsmiðurinn Honda hlaut í gær leyfi yfirvalda til að selja bíl með þriðja stigs sjálfaksturs tækni.",
        "Rómeó og Júlía er saga af sannri ást en um leið ástsýki og ungæðishætti. Í forgrunni verður mögnuð barátta ungrar konu gegn yfirþyrmandi feðraveldi. Fegurstu sögurnar geta sprottið upp úr hræðilegustu aðstæðunum.",
        "Diogo Jota, leikmaður Liverpool, er mjög ósáttur með EA Sports og sú einkunn sem þeir hafa gefið honum í FIFA 21 leiknum. EA Sports uppfærði ekki tölfræðina hans á þessu tímabili.",
    ]

    sentences = [
"Máltækni M S c",

"Með máltækni er þróaður búnaður sem getur unnið með og skilið náttúruleg tungumál og stuðlað að notkun þeirra í samskiptum manns og tölvu. Hverjir kannast ekki við tæki eða hugbúnað frá Apple, Amazon, Facebook, Google og Microsoft sem hægt er að stýra með tali eða texta",

"Spennandi störf á alþjóðlegum vettvangi",

"Að námi loknu ættu nemendur að geta starfað við hugbúnaðarþróun í máltækni eða á sviðum þar sem vélrænu námi er beitt.",

"Jafnframt ætti námið að skapa grundvöll fyrir störfum á alþjóðlegum vettvangi því eftirspurn eftir starfskröftum með þessa þekkingu er alltaf að aukast. Nægir hér að nefna að tæki eða hugbúnaður, sem stórfyrirtæki eins og Apple, Amazon, Facebook, Google og Microsoft þróa, krefjast þekkingar á máltækni.",

"M S c gráða ef námið er klárað í H R",

"Nemandi sem skráður er í H R útskrifast með M S c gráðu í máltækni en nemandi sem skráður er í H Í útskrifast með M A gráðu í máltækni. Sérstakar námsreglur gilda um meistaranámið í hvorum skóla fyrir sig og skulu nemendur lúta námsreglum heimaskóla síns.",

"Hægt að stunda doktorsnám",

"Markmið með náminu er tvíþætt, annars vegar að útskrifa nemendur með þekkingu til að stýra verkefnum og útfæra lausnir á sviði máltækni, hins vegar að undirbúa nemendur undir doktorsnám á sviðinu.",

"Skipulag námsins í H R",

"Um er að ræða tveggja ára, þverfaglegt, hundrað og tuttugu eininga nám. Einingarnar skiptast í fjörtíu og fjórar til sjötíu og átta einingar úr námskeiðum á meistarastigi, kennd í H R og H Í, núll til þrjátíu einingar úr grunnnámskeiðum í tölvunarfræði, núll til tíu einingar úr grunnnámskeiðum í málfræði, kennd í H Í, og þrjátíu til sextíu einingar í meistaraprófsverkefni, ritgerð. Samsetning eininga er því sveigjanleg og fer eftir bakgrunni viðkomandi nemanda.",

"Nemendur með B A próf í málvísindum og tungumálum þurfa að taka þrjátíu einingar í grunnnámskeiðum í tölvunarfræði. Þessi námskeið eru metin sem hluti meistaranámsins. Nemendur með aðra undirstöðu gætu þurft að taka grunnnámskeið í bæði málfræði og tölvunarfræði.",
    ]

    sentences_sol = [
"Sólskin",
"Þú ert mitt sólskyn. Mitt eina sólskyn. Þú gleður mig þegar himinn gránar.",
"Þú ert mitt sólskyn. Mitt eina sólskyn. Ekki taka sólskyn mér frááááá",
"Ég er hreiðruð settning",
"Ég er meira hreiðruð settning",
    ]

    model = get_FastSpeech2(args.step, full_path=args.model_fs).to(device)
    melgan = waveglow = None
    if hp.vocoder == 'melgan':
        melgan = utils.get_melgan(full_path=args.model_melgan)
        melgan.to(device)
    elif hp.vocoder == 'waveglow':
        waveglow = utils.get_waveglow()
        waveglow.to(device)
    g2p_model = load_g2p(args.model_g2p)

    for i, sentence in enumerate(sentences):
        text = preprocess(sentence, g2p_model)
        synthesize(model, waveglow, melgan, text, sentence, prefix='content-{}'.format(i+1))

    with torch.no_grad():
        for i, sentence in enumerate(sentences):
            text = preprocess(sentence, g2p_model)
            synthesize(model, waveglow, melgan, text, sentence, 'content-{}'.format(
                i+1), args.duration_control, args.pitch_control, args.energy_control)

