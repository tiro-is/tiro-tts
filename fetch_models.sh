#!/usr/bin/env bash

if [[ $# != 1 ]] || { [[ $1 != "test" ]] && [[ $1 != "dep" ]]; }; then
    echo "Please provide a single argument: \"test\" or \"dep\""
    exit 1
fi

echo "Fetching $1 models..."

if [[ $1 == "test" ]]; then
    mkdir -p models
else
    mkdir -p /models/
fi

STORAGE_ROOT="https://storage.googleapis.com/tiro-is-public-assets/models"

dl() {
  set -x
  mkdir -p $(dirname $2)
  curl "$1" -o "$2"
  set +x
}

ALFUR_FASTSPEECH_ORIGIN="$STORAGE_ROOT/tts/fastspeech2/v2021-01-01/checkpoint_490000_jit_quant_fbgemm_v2.pt"
ALFUR_MELGAN_ORIGIN="$STORAGE_ROOT/tts/fastspeech2/v2021-01-01/vocoder_aca5990_3350_jit_v2.pt"
DILJA_FASTSPEECH_ORIGIN="$STORAGE_ROOT/tts/fastspeech2/dilja/v2021-07-26/checkpoint_380000_jit_quant_fbgemm_v2.pt"
DILJA_MELGAN_ORIGIN="$STORAGE_ROOT/tts/fastspeech2/dilja/v2021-07-26/dilja_aca5990_4550_jit_v2.pt"
SEQUITUR_ORIGIN="$STORAGE_ROOT/g2p/is-IS.ipd_clean_slt2018.mdl"
LEXICON_ORIGIN="$STORAGE_ROOT/g2p/iceprondict/version_21.06/ice_pron_dict_standard_clear.csv"
SEQUITUR_FAIL_EN_ORIGIN="$STORAGE_ROOT/g2p/en-IS.cmudict_frobv1.20200305.mdl"
ALFUR_ESPNET2_ORIGIN="$STORAGE_ROOT/tts/espnet2/alfur/f_tts_train_fastspeech2_raw_phn_none_train.loss.ave.zip"
DILJA_ESPNET2_ORIGIN="$STORAGE_ROOT/tts/espnet2/dilja/c_tts_train_fastspeech2_raw_phn_none_train.loss.ave.zip"
MBMELGAN_ORIGIN="$STORAGE_ROOT/tts/espnet2/universal/mbmelgan.zip"

ALFUR_FASTSPEECH_DESTINATION="/models/alfur/fastspeech_jit.pt"
ALFUR_MELGAN_DESTINATION="/models/alfur/melgan_jit.pt"
DILJA_FASTSPEECH_DESTINATION="/models/dilja/fastspeech_jit.pt"
DILJA_MELGAN_DESTINATION="/models/dilja/melgan_jit.pt"
SEQUITUR_DESTINATION="/models/sequitur.mdl"
LEXICON_DESTINATION="/models/lexicon.txt"
SEQUITUR_FAIL_EN_DESTINATION="/models/sequitur_fail_en.mdl"

ALFUR_ESPNET2_DESTINATION="/models/alfur/espnet2.zip"
DILJA_ESPNET2_DESTINATION="/models/dilja/espnet2.zip"
MBMELGAN_DESTINATION="/models/universal/mbmelgan.zip"

if [[ $1 == "test" ]]; then
  SEQUITUR_DESTINATION=${SEQUITUR_DESTINATION:1}
  LEXICON_DESTINATION=${LEXICON_DESTINATION:1}
  ALFUR_MELGAN_DESTINATION=${ALFUR_MELGAN_DESTINATION:1}
  ALFUR_FASTSPEECH_DESTINATION=${ALFUR_FASTSPEECH_DESTINATION:1}
  ALFUR_ESPNET2_DESTINATION=${ALFUR_ESPNET2_DESTINATION:1}
  DILJA_ESPNET2_DESTINATION=${DILJA_ESPNET2_DESTINATION:1}
  MBMELGAN_DESTINATION=${MBMELGAN_DESTINATION:1}
fi

if [[ $1 == "dep" ]]; then
    dl $DILJA_FASTSPEECH_ORIGIN $DILJA_FASTSPEECH_DESTINATION
    dl $DILJA_MELGAN_ORIGIN $DILJA_MELGAN_DESTINATION
    dl $SEQUITUR_FAIL_EN_ORIGIN $SEQUITUR_FAIL_EN_DESTINATION
fi

dl $ALFUR_FASTSPEECH_ORIGIN $ALFUR_FASTSPEECH_DESTINATION
dl $ALFUR_MELGAN_ORIGIN $ALFUR_MELGAN_DESTINATION
dl $SEQUITUR_ORIGIN $SEQUITUR_DESTINATION
dl $LEXICON_ORIGIN $LEXICON_DESTINATION
dl $ALFUR_ESPNET2_ORIGIN $ALFUR_ESPNET2_DESTINATION
dl $DILJA_ESPNET2_ORIGIN $DILJA_ESPNET2_DESTINATION
dl $MBMELGAN_ORIGIN $MBMELGAN_DESTINATION

echo "Successfully finished fetching $1 models!"
