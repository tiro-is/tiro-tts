#!/usr/bin/env bash

if [[ $# != 1 ]] || { [[ $1 != "test" ]] && [[ $1 != "dep" ]]; }; then
    echo "Please provide a single argument: \"test\" or \"dep\""
    exit 1
fi

echo "Fetching $1 models..."

if [[ $1 == "test" ]]; then
    KEYFILE_PATH=$GCS_CREDS
else
    KEYFILE_PATH="/creds/keyfile.json"
fi

if [[ $1 == "test" ]]; then
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-370.0.0-linux-x86_64.tar.gz
    echo "0525cfa2a027da3fde18aeafe9c379c97f7b60b20ce3c97f8976a15982b76f62  google-cloud-sdk-370.0.0-linux-x86_64.tar.gz" | sha256sum -c
    tar --strip-components=1 -xf google-cloud-sdk-370.0.0-linux-x86_64.tar.gz -C /usr
fi

gcloud auth activate-service-account --key-file=$KEYFILE_PATH
if [[ $1 == "test" ]]; then
    mkdir -p models
else
    mkdir -p /models/
fi

ALFUR_FASTSPEECH_ORIGIN="gs://models-talgreinir-is/tts/fastspeech2/v2021-01-01/checkpoint_490000_jit_quant_fbgemm_v2.pt"
ALFUR_MELGAN_ORIGIN="gs://models-talgreinir-is/tts/fastspeech2/v2021-01-01/vocoder_aca5990_3350_jit_v2.pt"
DILJA_FASTSPEECH_ORIGIN="gs://models-talgreinir-is/tts/fastspeech2/dilja/v2021-07-26/checkpoint_380000_jit_quant_fbgemm_v2.pt"
DILJA_MELGAN_ORIGIN="gs://models-talgreinir-is/tts/fastspeech2/dilja/v2021-07-26/dilja_aca5990_4550_jit_v2.pt"
SEQUITUR_ORIGIN="gs://models-talgreinir-is/g2p/is-IS.ipd_clean_slt2018.mdl"
LEXICON_ORIGIN="gs://models-talgreinir-is/g2p/iceprondict/version_21.06/ice_pron_dict_standard_clear.csv#1624979739994321"
SEQUITUR_FAIL_EN_ORIGIN="gs://models-talgreinir-is/g2p/en-IS.cmudict_frobv1.20200305.mdl"

ALFUR_FASTSPEECH_DESTINATION="/models/alfur/fastspeech_jit.pt"
ALFUR_MELGAN_DESTINATION="/models/alfur/melgan_jit.pt"
DILJA_FASTSPEECH_DESTINATION="/models/dilja/fastspeech_jit.pt"
DILJA_MELGAN_DESTINATION="/models/dilja/melgan_jit.pt"
SEQUITUR_DESTINATION="/models/sequitur.mdl"
LEXICON_DESTINATION="/models/lexicon.txt"
SEQUITUR_FAIL_EN_DESTINATION="/models/sequitur_fail_en.mdl"

if [[ $1 == "test" ]]; then
  SEQUITUR_DESTINATION=${SEQUITUR_DESTINATION:1}
  LEXICON_DESTINATION=${LEXICON_DESTINATION:1}
  ALFUR_MELGAN_DESTINATION=${ALFUR_MELGAN_DESTINATION:1}
  ALFUR_FASTSPEECH_DESTINATION=${ALFUR_FASTSPEECH_DESTINATION:1}
fi

if [[ $1 == "dep" ]]; then
    gsutil cp $DILJA_FASTSPEECH_ORIGIN $DILJA_FASTSPEECH_DESTINATION
    gsutil cp $DILJA_MELGAN_ORIGIN $DILJA_MELGAN_DESTINATION
    gsutil cp $SEQUITUR_FAIL_EN_ORIGIN $SEQUITUR_FAIL_EN_DESTINATION
fi

gsutil cp $ALFUR_FASTSPEECH_ORIGIN $ALFUR_FASTSPEECH_DESTINATION
gsutil cp $ALFUR_MELGAN_ORIGIN $ALFUR_MELGAN_DESTINATION
gsutil cp $SEQUITUR_ORIGIN $SEQUITUR_DESTINATION
gsutil cp $LEXICON_ORIGIN $LEXICON_DESTINATION

echo "Successfully finished fetching $1 models!"
