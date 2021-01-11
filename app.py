import io
import contextlib
import uuid
import subprocess
from flask import Flask, jsonify, Response, send_from_directory
from flask_cors import CORS
from webargs import fields
from flask_apispec import use_kwargs, marshal_with, FlaskApiSpec, doc
from flask_caching import Cache
from marshmallow import validate, Schema
from apispec import APISpec, BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from config import EnvvarConfig
from aws import Polly

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
app.config["APISPEC_SWAGGER_UI_URL"] = "/"
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60 * 60 * 24 * 2
app.config.from_object(EnvvarConfig)

CORS(app)
cache = Cache(app)

g_polly = Polly()


class DisableOptionsOperationPlugin(BasePlugin):
    # See https://github.com/jmcarp/flask-apispec/issues/155#issuecomment-562542538
    def operation_helper(self, operations, **kwargs):
        # flask-apispec auto generates an options operation, which cannot handled by apispec.
        # apispec.exceptions.DuplicateParameterError: Duplicate parameter with name body and location body
        # => remove
        operations.pop("options", None)


app.config["APISPEC_SPEC"] = APISpec(
    title="TTS",
    version="v0",
    host=app.config["HOST"],
    openapi_version="2.0",
    plugins=[MarshmallowPlugin(), DisableOptionsOperationPlugin()],
    tags=[
        {"name": "speak", "description": "Generate waveform for phoneme strings."},
        {"name": "speech", "description": "Synthesize speech from input text"},
    ],
)
docs = FlaskApiSpec(app)


def speak_espeak(phoneme_string):
    app.logger.info("Speaking '{}'".format(phoneme_string))
    wav = subprocess.check_output(
        ["espeak-ng", "-v", "icelandic", "--stdout"],
        input="[[{}]]".format(phoneme_string).encode(),
    )
    return wav


def speak_espeak_to_file(phoneme_string) -> str:
    app.logger.info("Speaking '{}'".format(phoneme_string))
    filename = "{}.wav".format(uuid.uuid4())
    wav = subprocess.check_output(
        ["espeak-ng", "-v", "icelandic", "-w", "generated/{}".format(filename)],
        input="[[{}]]".format(phoneme_string).encode(),
    )
    return filename


class SpeakRequest(Schema):
    pronunciation = fields.Str(
        required=True,
        description="X-SAMPA phoneme string",
        example="r_0iNtI",
        validate=validate.Length(min=1, max=126),
    )


class SpeakResponse(Schema):
    pronunciation = fields.Str(
        required=True,
        description="X-SAMPA phoneme string",
        example="r_0iNtI",
        validate=validate.Length(min=1, max=126),
    )

    url = fields.Str(
        required=True,
        description="The URL for the generate WAV file",
        example=(
            "{}://{}/v0/speak/generated/82fb88cf-914b-41ac-ac1d-6519b2bf181b.wav".format(
                app.config["SCHEME"], app.config["HOST"]
            )
        ),
    )


@app.route("/v0/speak", methods=["POST", "OPTIONS"])
@use_kwargs(SpeakRequest)
@marshal_with(SpeakResponse)
@doc(description="Generate WAV file from phoneme string", tags=["speak"])
@cache.memoize()
def route_post_speak(pronunciation):
    filename = speak_espeak_to_file(pronunciation)

    return jsonify(
        {
            "pronunciation": pronunciation,
            "url": "{}://{}/v0/generated/{}".format(
                app.config["SCHEME"], app.config["HOST"], filename
            ),
        }
    )


docs.register(route_post_speak)


@app.route("/v0/speak", methods=["GET"])
@doc(
    description="Generate WAV file from phoneme string",
    produces=["audio/x-wav"],
    tags=["speak"],
)
@use_kwargs(
    {
        "q": fields.Str(
            required=True,
            description="X-SAMPA phoneme string",
            example="r_0iNtI",
            validate=validate.Length(min=1, max=126),
        ),
    },
    location="query",
)
@marshal_with(None)
@cache.memoize()
def route_speak(q):
    return Response(response=speak_espeak(q), content_type="audio/x-wav")


docs.register(route_speak)


@app.route("/v0/generated/<filename>", methods=["GET", "OPTIONS"])
@marshal_with(None)
@doc(
    produces=["audio/x-wav"], tags=["speak"],
)
def route_serve_generated_speech(filename):
    return send_from_directory("generated", filename)


docs.register(route_serve_generated_speech)


class SynthesizeSpeechRequest(Schema):
    Engine = fields.Str(
        required=True,
        description="Specify which engine to use",
        validate=validate.OneOf(["standard"]),
    )
    LanguageCode = fields.Str(required=False, example=None)
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
        example=None,
    )
    OutputFormat = fields.Str(
        required=True,
        description=(
            " The format in which the returned output will be encoded. "
            + "For audio stream, this will be mp3, ogg_vorbis, or pcm. "
            + "For speech marks, this will be json. "
        ),
        validate=validate.OneOf(["json", "pcm", "mp3", "ogg_vorbis"]),
        example="mp3",
    )
    SampleRate = fields.Str(
        required=True,
        description="The audio frequency specified in Hz.",
        validate=validate.OneOf(["8000", "16000", "22050", "24000"]),
        example="16000",
    )
    SpeechMarkTypes = fields.List(
        fields.Str(validate=validate.OneOf(["sentence", "ssml", "viseme", "word"])),
        required=False,
        description="The type of speech marks returned for the input text",
        example=None,
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
        validate=validate.OneOf(["text", "ssml"]),
    )
    VoiceId = fields.Str(
        required=True,
        description="Voice ID to use for the synthesis",
        validate=validate.OneOf(["Dora", "Karl"]),
    )


@app.route("/v0/speech", methods=["POST", "OPTIONS"])
@use_kwargs(SynthesizeSpeechRequest)
@doc(
    description="Synthesize speech",
    tags=["speech"],
    produces=["audio/mpeg", "audio/ogg", "application/x-json-stream",],
)
@cache.memoize()
def route_synthesize_speech(**kwargs):
    app.logger.info("Got request: %s", kwargs)
    polly_resp = g_polly.synthesize_speech(**kwargs)

    output_content_type = "application/x-json-stream"
    if kwargs["OutputFormat"] == "mp3":
        output_content_type = "audio/mpeg"
    elif kwargs["OutputFormat"] == "ogg_vorbis":
        output_content_type = "audio/ogg"

    try:
        if "AudioStream" in polly_resp:
            with contextlib.closing(polly_resp["AudioStream"]) as stream:
                content = stream.read()
            return Response(content, content_type=output_content_type)
        else:
            return {"error": 1}, 400
    except:
        return {"error": 1}, 400


docs.register(route_synthesize_speech)
