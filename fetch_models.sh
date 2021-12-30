#!/bin/bash -xeu

mkdir -p models
gcloud auth activate-service-account --key-file=/creds/keyfile.json

ALFUR_FASTSPEECH=gs://models-talgreinir-is/tts/fastspeech2/v2021-01-01/checkpoint_490000_jit_quant_fbgemm.pt
ALFUR_MELGAN=gs://models-talgreinir-is/tts/fastspeech2/v2021-01-01/vocoder_aca5990_3350_jit.pt

DILJA_FASTSPEECH=gs://models-talgreinir-is/tts/fastspeech2/dilja/v2021-07-26/checkpoint_380000_jit_quant_fbgemm.pt
DILJA_MELGAN=gs://models-talgreinir-is/tts/fastspeech2/dilja/v2021-07-26/dilja_aca5990_4550_jit.pt

SEQUITUR=gs://models-talgreinir-is/g2p/is-IS.ipd_clean_slt2018.mdl
LEXICON=gs://models-talgreinir-is/g2p/iceprondict/version_21.06/ice_pron_dict_standard_clear.csv#1624979739994321
SEQUITUR_FAIL_EN=gs://models-talgreinir-is/g2p/en-IS.cmudict_frobv1.20200305.mdl

gsutil cp $ALFUR_FASTSPEECH /models/alfur/fastspeech_jit.pt
gsutil cp $ALFUR_MELGAN /models/alfur/melgan_jit.pt

gsutil cp $DILJA_FASTSPEECH /models/dilja/fastspeech_jit.pt
gsutil cp $DILJA_MELGAN /models/dilja/melgan_jit.pt

gsutil cp $SEQUITUR /models/sequitur.mdl
gsutil cp $LEXICON /models/lexicon.txt
gsutil cp $SEQUITUR_FAIL_EN /models/sequitur_fail_en.mdl