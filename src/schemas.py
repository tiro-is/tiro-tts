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
                 "Text": " Góðan, dag. Hvað heitir þú? Kvöld-Úlfur.",
                 "VoiceId": "Other"
                }

            might return

                {"time": 54, "type": "word", "start": 1, "end": 9, "value": "Góðan,"}
                {"time": 44, "type": "word", "start": 10, "end": 14, "value": "dag."}
                {"time": 26, "type": "word", "start": 15, "end": 20, "value": "Hvað"}
                {"time": 33, "type": "word", "start": 21, "end": 27, "value": "heitir"}
                {"time": 19, "type": "word", "start": 28, "end": 33, "value": "þú?"}
                {"time": 88, "type": "word", "start": 34, "end": 48, "value": "Kvöld-Úlfur."}

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
        description=(
            "Specifies whether the input text is plain text or SSML. "
            + "The default value is plain text. "
            + "\n\n"
            + "Currently the SSML support is restricted to just `<phoneme>` tags, e.g:<br>"
            + "`<speak>Ég er <phoneme alphabet='x-sampa' ph='...'>gervimaður</phoneme></speak>`"
            + "\n\n"
            + "Currently only plain text requests are normalized before synthesis."
        ),
        validate=validate.OneOf(["text", "ssml"]),
    )
    VoiceId = fields.Str(
        required=True,
        description="Voice ID to use for the synthesis",
        example="Other",
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


class Voice(Schema):
    VoiceId = fields.Str(example="Other")

    Gender = fields.Str(validate=validate.OneOf(["Male", "Female"]))

    LanguageCode = fields.Str(example="is-IS")

    LanguageName = fields.Str(example="Íslenska")

    SupportedEngines = fields.List(fields.Str(validate=validate.OneOf(["standard"])))


class Error(Schema):
    message = fields.Str(required=True)
