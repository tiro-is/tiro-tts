# Copyright 2021 Tiro ehf.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF AbNY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import textwrap

from marshmallow import Schema, validate
from webargs import fields


class SynthesizeSpeechRequest(Schema):
    Engine = fields.Str(
        required=False,
        description="Specify which engine to use",
        validate=validate.OneOf(["standard"]),
    )
    LanguageCode = fields.Str(required=False, example="is-IS")
    LexiconNames = fields.List(
        fields.Str(),
        required=False,
        description=(
            "List of one or more pronunciation lexicon names you want the "
            + "service to apply during synthesis. Lexicons are applied only if the "
            + "language of the lexicon is the same as the language of the voice. "
            + "For information about storing lexicons, see PutLexicon. "
            + "UNIMPLEMENTED"
        ),
        example=[],
    )
    OutputFormat = fields.Str(
        required=True,
        description=(
            " The format in which the returned output will be encoded. "
            + "For audio stream, this will be mp3, ogg_vorbis, or pcm. "
            + "For speech marks, this will be json. "
        ),
        validate=validate.OneOf(["json", "pcm", "mp3", "ogg_vorbis"]),
        example="pcm",
    )
    SampleRate = fields.Str(
        required=False,
        description=textwrap.dedent(
            """\
            The audio frequency specified in Hz. Output formats `mp3` and
            `ogg_vorbis` support the all sample rates.
            """
        ),
        validate=validate.OneOf(["8000", "16000", "22050"]),
        example="22050",
    )
    SpeechMarkTypes = fields.List(
        # "sentence", "ssml", "viseme",
        fields.Str(validate=validate.OneOf(["word"])),
        required=False,
        description=textwrap.dedent(
            """\
            The type of speech marks returned for the input text.

            Only word level speech marks are supported, which contain the start
            time of each word and their start and end byte offsets in the input
            text. E.g.

                {
                 "Engine": "standard",
                 "LanguageCode": "is-IS",
                 "OutputFormat": "json",
                 "SpeechMarkTypes": ["word"],
                 "Text": "Hæ! Ég heiti Gervimaður Finnland, en þú?",
                 "VoiceId": "Alfur"
                }

            might return

                {"time": 0, "type": "word", "start": 0, "end": 3, "value": "Hæ"}
                {"time": 186, "type": "word", "start": 5, "end": 8, "value": "Ég"}
                {"time": 342, "type": "word", "start": 9, "end": 14, "value": "heiti"}
                {"time": 662, "type": "word", "start": 15, "end": 26, "value": "Gervimaður"}
                {"time": 1227, "type": "word", "start": 27, "end": 35, "value": "Finnland"}
                {"time": 1905, "type": "word", "start": 37, "end": 39, "value": "en"}
                {"time": 2055, "type": "word", "start": 40, "end": 44, "value": "þú"}

            On tts.tiro.is speech marks are only available for the voices: Alfur, Dilja,
            Karl and Dora.

            """
        ),
        example=["word"],
    )
    Text = fields.Str(
        required=True,
        description="Input text to synthesize.",
        example="Halló! Ég er gervimaður.",
        validate=validate.Length(min=1, max=3000),
    )
    TextType = fields.Str(
        required=False,
        description=textwrap.dedent(
            """\
            Specifies whether the input text is plain text or SSML. The default value is
            plain text.

            <a name="supported-ssml-tags"></a>
            ## Supported SSML tags

            The following tags are supported:

            ### `<speak>`

            This is the required root element of all SSML requests.

            ```xml
            <speak>Hæ! Ég heiti Gervimaður Finnland, en þú?</speak>
            ```

            Note that nesting tags is currently not supported. That means that the
            following is not supported, where we try to increase the speech rate of a
            sentence that uses a custom phonetic pronunciation:

            ```xml
            <speak>
              <prosody rate='150%'>Ég er <phoneme alphabet='x-sampa' ph='cErvIm9i:r'>
              gervimaður</phoneme></prosody>.
            </speak>
            ```

            ### `<phoneme>`

            This tag can be used to specify a certain phonetic pronunciation of a word
            or phrase. It requires the use of two attributes:

            - `alphabet`: We currently only support `x-sampa` which indicates the use
              of X-SAMPA, or the specific subset the voice supports.
            - `ph`: Specifies the phonetic symbols.

            ```xml
            <speak>
              Ég er <phoneme alphabet='x-sampa' ph='cErvIm9i:r'>gervimaður</phoneme>
            </speak>
            ```

            ### `<prosody>`

            The prosody tag can be used to control the pitch, volume and rate of
            speech. Each of these attributes vary somewhat beetween voices, so they are
            all relative.

            The availabe attributes are:

            - `volume`:
              - `silent`, `x-soft`, `soft`, `medium`, `loud`, `x-loud`
              - `+ndB` or `-ndB`: Change the volume relative to the current volume in
                decibels.

            ```xml
            <speak>
              <prosody volume='loud'>Hæ!</prosody> Ég heiti Gervimaður Finnland, en þú?
            </speak>
            ```

            - `rate`:
              - `x-slow`, `slow`, `medium`, `fast`, `x-fast`
              - `n%`: A percentage in the range 20-200% where 50% means half of the
                default speaking rate and 200% means twice the default speaking rate.

            ```xml
            <speak>
              Hæ! Ég heiti Gervimaður Finnland, en þú? <prosody rate='150%'>Hvað
              sagðirðu?</prosody>
            </speak>
            ```

            - `pitch`:
              - `x-low`, `low`, `medium`, `high`, `x-high`
              - `+n%` or `-n%`: Shift the pitch up or down by a specific percentage.

            ```xml
            <speak>
              Hæ! Ég heiti Gervimaður Finnland, en þú? <prosody pitch='x-low'>Ég er bara
              Gervimaður Útlönd</prosody>
            </speak>
            ```

            These three attributes can be combined, as so:

            ```xml
            <speak>
              <prosody volume='x-loud' pitch='high' rate='140%'>Hæ!</prosody> Ég heiti
              Gervimaður Finnland, en þú?
            </speak>
            ```

            ### `<say-as>`

            It is possible to control how certain words are interpreted with the
            `interpret-as` attribute of the `<say-as>` tag. The following values
            currently supported for `interpret-as`:

            - `digits`: Spells out each digit individually.
            - `characters` or `spell-out`: Spells out each letter individually.

            ```xml
            <speak>
              Gervimaður Útlönd vill ekki sjá <say-as interpret-as='spell-out'>ehf
              </say-as>. Hann hringir bara í <say-as interpret-as='digits'>112</say-as>.
            </speak>
            ```

            ### `<sub>`

            The `alias` attribute of the `<sub>` tag can used to substitute a different
            word for a word or phrase, an abbreviation for example.

            ```xml
            <speak>
              Gervimaður Finnland vill setja 10 <sub alias='míkrópasköl á
              rúmsentímetra'>µPa/cc</sub> af þessu í vatnið.
            </speak>
            ```

            """
        ),
        validate=validate.OneOf(["text", "ssml"]),
    )
    VoiceId = fields.Str(
        required=True,
        description="Voice ID to use for the synthesis",
        example="Alfur",
    )


class DescribeVoicesRequest(Schema):
    Engine = fields.Str(
        description="Specify which engine to use",
        validate=validate.OneOf(["standard"]),
    )

    LanguageCode = fields.Str(
        required=False,
        description=(
            "The language identification tag (ISO 639 code for the language "
            + "name-ISO 3166 country code) for filtering the list of voices "
            + "returned. If you don't specify this optional parameter, all available"
            + " voices are returned. "
        ),
        example="is-IS",
    )

    ExtraMetadata = fields.Bool(
        required=False,
        description=textwrap.dedent(
            """\
            Whether to include extra metadata for each voice, e.g. model versions/hashes.
            """
        ),
    )


class VoiceMetadata(Schema):
    VoiceVersion = fields.Str(required=False)


class Voice(Schema):
    VoiceId = fields.Str(example="Alfur")

    Gender = fields.Str(validate=validate.OneOf(["Male", "Female"]))

    LanguageCode = fields.Str(example="is-IS")

    LanguageName = fields.Str(example="Íslenska")

    SupportedEngines = fields.List(fields.Str(validate=validate.OneOf(["standard"])))

    ExtraMetadata = fields.Nested(VoiceMetadata)


class Error(Schema):
    message = fields.Str(required=True)
