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
from lib.fastspeech.align_phonemes import Aligner
from fastspeech import FastSpeech2Synthesizer, XSAMPA_IPA_MAP


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
app.config["APISPEC_SWAGGER_UI_URL"] = "/"
app.config.from_object(EnvvarConfig)

cors = CORS(app)
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


def speak_espeak_to_file(phoneme_string: str, filename: str) -> None:
    wav = subprocess.check_output(
        ["espeak-ng", "-v", "icelandic", "-w", "generated/{}".format(filename)],
        input="[[{}]]".format(phoneme_string).encode(),
    )


def speak_polly(phoneme_string: str) -> bytes:
    ssml_content = """
    <speak>
      <phoneme alphabet='x-sampa' ph='{phoneme_string}'>{phoneme_string}</phoneme>
    </speak>
    """.format(
        phoneme_string=phoneme_string
    )
    polly_resp = g_polly.synthesize_speech(
        Engine="standard",
        SampleRate="16000",
        Text=ssml_content,
        TextType="ssml",
        VoiceId="Dora",
        OutputFormat="mp3",
    )

    content = b""
    if "AudioStream" in polly_resp:
        with contextlib.closing(polly_resp["AudioStream"]) as stream:
            content = stream.read()
    return content


def speak_polly_to_file(phoneme_string: str, filename: str) -> None:
    ssml_content = """
    <speak>
      <phoneme alphabet='x-sampa' ph='{phoneme_string}'>{phoneme_string}</phoneme>
    </speak>
    """.format(
        phoneme_string=phoneme_string
    )
    polly_resp = g_polly.synthesize_speech(
        Engine="standard",
        SampleRate="16000",
        Text=ssml_content,
        TextType="ssml",
        VoiceId="Dora",
        OutputFormat="mp3",
    )

    if "AudioStream" in polly_resp:
        with contextlib.closing(polly_resp["AudioStream"]) as stream, open(
            "generated/{}".format(filename), "wb"
        ) as f:
            f.write(stream.read())


g_fastspeech = FastSpeech2Synthesizer()


def speak_fs(phoneme_string: str):
    phoneme_string = " ".join(
        XSAMPA_IPA_MAP[phn]
        for phn in Aligner(phoneme_set=set(XSAMPA_IPA_MAP.keys()))
        .align(phoneme_string)
        .split(" ")
    )
    content = io.BytesIO()
    g_fastspeech.synthesize("{" + phoneme_string + "}", content)
    return content


def speak_fs_to_file(phoneme_string: str, filename: str) -> None:
    phoneme_string = " ".join(
        XSAMPA_IPA_MAP[phn]
        for phn in Aligner(phoneme_set=set(XSAMPA_IPA_MAP.keys()))
        .align(phoneme_string)
        .split(" ")
    )
    g_fastspeech.synthesize("{" + phoneme_string + "}", filename)


def speak_phoneme_to_file(phoneme_string: str) -> str:
    app.logger.info("Speaking '{}'".format(phoneme_string))
    filename = "{}.wav".format(uuid.uuid4())
    speak_fs_to_file(phoneme_string, "generated/{}".format(filename))
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


@app.route("/v0/speak", methods=["POST"])
@use_kwargs(SpeakRequest)
@marshal_with(SpeakResponse)
@doc(description="Generate WAV file from phoneme string", tags=["speak"])
@cache.memoize()
def route_post_speak(pronunciation):

    filename = speak_phoneme_to_file(pronunciation)

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
    description="Generate audio file from phoneme string",
    produces=["audio/x-wav", "audio/mpeg"],
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
    return Response(response=speak_fs(q), content_type="audio/mpeg")


docs.register(route_speak)


@app.route("/v0/generated/<filename>", methods=["GET"])
@marshal_with(None)
@doc(
    produces=["audio/x-wav", "audio/mpeg"], tags=["speak"],
)
def route_serve_generated_speech(filename):
    return send_from_directory("generated", filename)


docs.register(route_serve_generated_speech)


SUPPORTED_VOICE_IDS = ["Dora", "Karl", "Other", "Joanna"]


class SynthesizeSpeechRequest(Schema):
    Engine = fields.Str(
        required=True,
        description="Specify which engine to use",
        validate=validate.OneOf(["standard", "neural"]),
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
        validate=validate.OneOf(["Dora", "Karl", "Other"]),
        validate=validate.OneOf(SUPPORTED_VOICE_IDS),
        example="Other",
    )


@app.route("/v0/speech", methods=["POST"])
@use_kwargs(SynthesizeSpeechRequest)
@doc(
    description="Synthesize speech",
    tags=["speech"],
    produces=["audio/mpeg", "audio/ogg", "application/x-json-stream", "audio/x-wav"],
)
@cache.memoize()
def route_synthesize_speech(**kwargs):
    app.logger.info("Got request: %s", kwargs)

    output_content_type = "application/x-json-stream"
    if kwargs["OutputFormat"] == "mp3":
        output_content_type = "audio/mpeg"
    elif kwargs["OutputFormat"] == "ogg_vorbis":
        output_content_type = "audio/ogg"
    elif kwargs["OutputFormat"] == "pcm":
        output_content_type = "audio/x-wav"

    if kwargs["VoiceId"] in ("Dora", "Karl", "Joanna"):
        polly_resp = g_polly.synthesize_speech(**kwargs)
        try:
            if "AudioStream" in polly_resp:
                with contextlib.closing(polly_resp["AudioStream"]) as stream:
                    content = stream.read()
                return Response(content, content_type=output_content_type)
            else:
                return {"error": 1}, 400
        except:
            return {"error": 1}, 400
    else:
        if kwargs["OutputFormat"] != "pcm" or kwargs["TextType"] != "text":
            return {"error": 1, "message": "Unsupported arguments"}, 400
        content = io.BytesIO()
        g_fastspeech.synthesize(kwargs["Text"], content)
        return Response(content, content_type=output_content_type)


docs.register(route_synthesize_speech)

if __name__ == '__main__':
    app.run()
