# Tiro talgervill / Tiro TTS

Works with a FastSpeech2+Melgan+Sequitur backend by default. See the
[cadia-lvl/FastSpeech2](https://github.com/cadia-lvl/FastSpeech2/tree/080603e6707ae4b8eae6832db7220116e4b4df3b)
repo.

The models used are configured with a text
[SynthesisSet](proto/tiro/tts/voice.proto) protobuf message supplied via the
environment variable `TIRO_TTS_SYNTHESIS_SET_PB`. See
[conf/synthesis_set.local.pbtxt](conf/synthesis_set.local.pbtxt) for an example.

## Normalization

There are two types of normalization referenced in
[voice.proto](proto/tiro/tts/voice.proto): `BasicNormalizer` and
`GrammatekNormalizer`.  `BasicNormalizer` is local and only handles stripping
punctuation but the `GrammatekNormalizer` is a gRPC service that implements
[`com.grammatek.tts_frontent.TTSFrontend`](https://github.com/grammatek/tts-frontend-api/blob/54ae2943375dd368ea94e5d869f71bdcc671a3cd/services/tts_frontend_service.proto),
such as
[grammatek/tts-frontend-service](https://github.com/grammatek/tts-frontend-service).


## License

Tiro TTS is licensed under the Apache License, Version 2.0. See
[LICENSE](LICENSE) for more details. Some individual files may be licensed under
different licenses, according to their headers.

## Acknowledgements

This project was funded by the Language Technology Programme for Icelandic
2019-2023. The programme, which is managed and coordinated by Almannarómur, is
funded by the Icelandic Ministry of Education, Science and Culture.
