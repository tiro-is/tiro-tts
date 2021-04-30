from flask import current_app
from marshmallow import validate, Schema
from webargs import fields

SUPPORTED_VOICE_IDS = ["Dora", "Karl", "Other", "Joanna"]


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
        required=True,
        description="The audio frequency specified in Hz.",
        validate=validate.OneOf(["8000", "16000", "22050", "24000"]),
        example="22050",
    )
    SpeechMarkTypes = fields.List(
        fields.Str(validate=validate.OneOf(["sentence", "ssml", "viseme", "word"])),
        required=False,
        description="The type of speech marks returned for the input text",
        example=[],
    )
    Text = fields.Str(
        required=True,
        description="Input text to synthesize.",
        example="Halló! Ég er gervimaður.",
    )
    TextType = fields.Str(
        required=False,
        description=(
            "Specifies whether the input text is plain text or SSML. "
            + "The default value is plain text. For more information, see Using SSML. "
        ),
        validate=validate.OneOf(["text",]),  # "ssml"
    )
    VoiceId = fields.Str(
        required=True,
        description="Voice ID to use for the synthesis",
        validate=validate.OneOf(SUPPORTED_VOICE_IDS),
        example="Other",
    )
