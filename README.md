# Tiro talgervill / Tiro TTS

Tiro TTS is a text-to-speech API server which works with various TTS backends.

The service can accept either unnormalized text or a [SSML](https://www.w3.org/TR/speech-synthesis11/) document and respond with audio (MP3, Ogg Vorbis or raw 16 bit PCM) or speech marks, indicating the byte and time offset of each synthesized word in the request. 

The full API documentation in OpenAPI 2 format is available online at
[tts.tiro.is](https://tts.tiro.is/). The documentation is auto-generated from
[src/schema.py](src/schema.py).

Tiro talgervill er vefþjónusta fyrir talgervingu sem styður nokkra mismunandi
bakenda. Þjónustan getur tekið við annað hvort ónormuðum texta eða
[SSML](https://www.w3.org/TR/speech-synthesis11/)-skjali og svarað með hljóðskrá
(MP3, Ogg Vorbis eða 16 bita PCM) eða *speech marks* sem gefa til kynna
tímasetningar og staðsetningu hvers orðs í innsenda textanum.

Skjölun forritunarskila þjónustunnar á OpenAPI 2 sniði er að finna á
[tts.tiro.is](https://tts.tiro.is/), en hún er búin til út frá
[src/schema.py](src/schema.py).

## Voices

The models used are configured with a text [SynthesisSet](proto/tiro/tts/voice.proto) protobuf message supplied via the
environment variable `TIRO_TTS_SYNTHESIS_SET_PB`. See [conf/synthesis_set.local.pbtxt](conf/synthesis_set.local.pbtxt) for an example. 

There are currently four voices accessible at [tts.tiro.is](https://tts.tiro.is/).

- Diljá: Female voice developed by Reykjavík University (FastSpeech2 + MelGAN).
- Diljá v2: Female voice developed by Reykjavík University (ESPnet2 FastSpeech2 + Multiband MelGAN).
- Álfur: Male voice developed by Reykjavík University (FastSpeech2 + MelGAN).
- Álfur v2: Male voice developed by Reykjavík University (ESPnet2 FastSpeech2 + Multiband MelGAN).
- Bjartur: Male voice developed by Reykjavík University (ESPnet2 FastSpeech2 + Multiband MelGAN).
- Rósa: Female voice developed by Reykjavík University (ESPnet2 FastSpeech2 + Multiband MelGAN).
- Karl: Male voice on Amazon Polly.
- Dóra: Female voice on Amazon Polly.

## Supported backends

The supported voice backends are described in
[voice.proto](proto/tiro/tts/voice.proto). There are three different backends:
`Fastspeech2MelganBackend`, `Espnet2Backend` and a AWS Polly proxy backend
`PollyBackend`.

### Model preparation for Fastspeech2MelganBackend

The backend [`tiro.tts.Fastspeech2MelganBackend`](proto/tiro/tts/voice.proto)
uses models created with
[cadia-lvl/FastSpeech2](https://github.com/cadia-lvl/FastSpeech2/tree/080603e6707ae4b8eae6832db7220116e4b4df3b)
and a vocoder created with
[seungwonpark/melgan](https://github.com/seungwonpark/melgan). Both the
FastSpeech2 and MelGAN models have to be converted to TorchScript models before
use. The converted models can also be downloaded:

- [Álfur Fastspeech2 acoustic model optimized for x86 CPU inference](https://storage.googleapis.com/tiro-is-public-assets/models/tts/fastspeech2/v2021-01-01/checkpoint_490000_jit_quant_fbgemm_v2.pt)
- [Diljá Fastspeech2 acoustic model optimized for x86 CPU inference](https://storage.googleapis.com/tiro-is-public-assets/models/tts/fastspeech2/dilja/v2021-07-26/checkpoint_380000_jit_quant_fbgemm_v2.pt)
- [Álfur MelGAN vocoder](https://storage.googleapis.com/tiro-is-public-assets/models/tts/fastspeech2/v2021-01-01/vocoder_aca5990_3350_jit_v2.pt)
- [Diljá MelGAN vocoder](https://storage.googleapis.com/tiro-is-public-assets/models/tts/fastspeech2/dilja/v2021-07-26/dilja_aca5990_4550_jit_v2.pt)

#### Converting the MelGAN vocoder

To convert the vocoder to TorchScript you have to have access to the trained
model and the audio files used to train it. There are two scripts necessary for
the conversion [//:melgan\_preprocess](src/lib/fastspeech/melgan/preprocess.py)
and [//:melgan\_convert](src/scripts/melgan_convert.py).

For the Diljá voice models from Reykjavik University (yet to be published) the
steps to prepare the TorchScript MelGAN vocoder are:

Download the recordings:

    mkdir wav
    wget https://repository.clarin.is/repository/xmlui/bitstream/handle/20.500.12537/104/dilja.zip
    unzip dilja.zip -d wav

Generate the input features:

    bazel run :melgan_preprocess -- -c $PWD/src/lib/fastspeech/melgan/config/default.yaml -d $PWD/wav/c

Convert the vocoder model:

    bazel run :melgan_convert -- -p $PATH_TO_ORIGNAL_MODEL -o $PWD/melgan_jit.pt -i $PWD/wav/c/audio

And then set `melgan_uri` in
[conf/synthesis\_set.local.pbtxt](conf/synthesis_set.local.pbtxt) to the path to
`melgan_jit.pt`.

#### Converting the FastSpeech2 acoustic model

The model is converted to TorchScript using scripting, so no recordings are
necessary. The script
[//:fastspeech\_convert](src/scripts/fastspeech_convert.py) can be used to
convert the model:

    bazel run :fastspeech_convert -- -p $PATH_TO_ORIGNAL_MODEL -o $PWD/fastspeech_jit.pt

And then set `fastspeech2_uri` in
[conf/synthesis\_set.local.pbtxt](conf/synthesis_set.local.pbtxt) to the path to
`fastspeech_jit.pt`.


## Normalization

There are two types of normalization referenced in [voice.proto](proto/tiro/tts/voice.proto): `BasicNormalizer` and
`GrammatekNormalizer`.  `BasicNormalizer` is local and only handles stripping punctuation but the `GrammatekNormalizer` is a gRPC service that implements [`com.grammatek.tts_frontent.TTSFrontend`](https://github.com/grammatek/tts-frontend-api/blob/54ae2943375dd368ea94e5d869f71bdcc671a3cd/services/tts_frontend_service.proto),
such as [grammatek/tts-frontend-service](https://github.com/grammatek/tts-frontend-service).

## Configuration

The voices are configured using Protobuf text file specified by
[voice.proto](proto/tiro/tts/voice.proto). By default it is loaded from
`conf/synthesis_set.pbtxt` but this can be changed by setting the environment
variable `TIRO_TTS_SYNTHESIS_SET_PB`. See [src/config.py](src/config.py) for a
complete list of possible environment variables.

## Building and running

The project requires Python 3.8 and uses Bazel for building. To build and run a
local development server use the script [./run.sh](./run.sh).

Docker can also be used to build the project:

    docker build -t tiro-tts .


and then to run the server:

    docker run -v DIR_WITH_MODELS:/models -v PATH_TO_SYNTHESIS_SET:/app/conf/synthesis_set.pbtxt \
               -p 8000:8000 tiro-tts

The project uses To build and run a local development server use the script run.sh.

## License

Tiro TTS is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for more details. Some individual files may be licensed under different licenses, according to their headers.

## Acknowledgments

This project was funded by the Language Technology Programme for Icelandic 2019-2023. The programme, which is managed and coordinated by Almannarómur, is funded by the Icelandic Ministry of Education, Science and Culture.
