# Tiro talgervill / Tiro TTS

Tiro TTS is a text-to-speech API server which works with various TTS backends. By default it expectes a FastSpeech2+Melgan+Sequitur backand. See the [cadia-lvl/FastSpeech2](https://github.com/cadia-lvl/FastSpeech2/tree/080603e6707ae4b8eae6832db7220116e4b4df3b) repo. 

The service can accept either unnormalized text or a [SSML](https://www.w3.org/TR/speech-synthesis11/) document and respond with audio (MP3, Ogg Vorbis or raw 16 bit PCM) or speech marks, indicating the byte and time offset of each synthesized word in the request. At the moment the SSML support is limited to the <phoneme> tag where the caller can use a subset of X-SAMPA to control the pronunciation of individual words or phrases in the request.

The full API documentation is avalible on [tts.tiro.is](https://tts.tiro.is/).

## Voices

The models used are configured with a text [SynthesisSet](proto/tiro/tts/voice.proto) protobuf message supplied via the
environment variable `TIRO_TTS_SYNTHESIS_SET_PB`. See [conf/synthesis_set.local.pbtxt](conf/synthesis_set.local.pbtxt) for an example. 

There are currently four voices accessible at [tts.tiro.is](https://tts.tiro.is/). 
- Diljá: Female voice developed by Reykjavík University.
- Álfur: Male voice developed by Reykjavík University. 
- Karl: Male voice on Amazon Polly.
- Dóra: Femal voice on Amazon Polly.

## Normalization

There are two types of normalization referenced in [voice.proto](proto/tiro/tts/voice.proto): `BasicNormalizer` and
`GrammatekNormalizer`.  `BasicNormalizer` is local and only handles stripping punctuation but the `GrammatekNormalizer` is a gRPC service that implements [`com.grammatek.tts_frontent.TTSFrontend`](https://github.com/grammatek/tts-frontend-api/blob/54ae2943375dd368ea94e5d869f71bdcc671a3cd/services/tts_frontend_service.proto),
such as [grammatek/tts-frontend-service](https://github.com/grammatek/tts-frontend-service).

## Bulding 

To build and run a local development server use the script run.sh.

## Model preparation

The backend [`tiro.tts.Fastspeech2MelganBackend`](proto/tiro/tts/voice.proto)
uses models created with
[cadia-lvl/FastSpeech2](https://github.com/cadia-lvl/FastSpeech2/tree/080603e6707ae4b8eae6832db7220116e4b4df3b)
and a vocoder created with
[seungwonpark/melgan](https://github.com/seungwonpark/melgan) that has been
converted to a TorchScript model. To convert the vocoder to TorchScript you have
to have access to the trained model and the audio files used to train it. There
are two scripts necessary for the conversion
[//:melgan\_preprocess](src/lib/fastspeech/melgan/preprocess.py) and
[//:melgan\_convert](src/scripts/melgan_convert.py).

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

And then set `melgan_uri`
[conf/synthesis_set.local.pbtxt](conf/synthesis_set.local.pbtxt) in to the path
to `melgan_jit.pt`.


## License

Tiro TTS is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for more details. Some individual files may be licensed under different licenses, according to their headers.

## Acknowledgements

This project was funded by the Language Technology Programme for Icelandic 2019-2023. The programme, which is managed and coordinated by Almannarómur, is funded by the Icelandic Ministry of Education, Science and Culture.