import os
import uuid
import json
import re
import subprocess
import logging
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from webargs import fields
from flask_apispec import use_kwargs, marshal_with, FlaskApiSpec, doc
from flask_caching import Cache
from marshmallow import validate, Schema
from apispec import APISpec, BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from typing import Dict, List
from config import EnvvarConfig

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
app.config["APISPEC_SWAGGER_UI_URL"] = "/"
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60*60*24*2
app.config.from_object(EnvvarConfig)

CORS(app)
cache = Cache(app)

# See https://github.com/jmcarp/flask-apispec/issues/155#issuecomment-562542538
class DisableOptionsOperationPlugin(BasePlugin):
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
        {"name": "speak",
         "description": "Generate waveform for phoneme strings."},
    ],
)
docs = FlaskApiSpec(app)


def speak_espeak(phoneme_string):
    logging.info("Speaking '{}'".format(phoneme_string))
    wav = subprocess.check_output(
        ["espeak-ng", "-v", "icelandic", "--stdout"],
        input="[[{}]]".format(phoneme_string).encode()
    )
    return wav

def speak_espeak_to_file(phoneme_string) -> str:
    logging.info("Speaking '{}'".format(phoneme_string))
    filename = "{}.wav".format(uuid.uuid4())
    wav = subprocess.check_output(
        ["espeak-ng",
         "-v", "icelandic",
         "-w", "generated/{}".format(filename)],
        input="[[{}]]".format(phoneme_string).encode()
    )
    return filename


class SpeakRequest(Schema):
    pronunciation = fields.Str(
        required=True,
        description="X-SAMPA phoneme string",
        example='r_0iNtI',
        validate=validate.Length(min=1, max=126)
    )

class SpeakResponse(Schema):
    pronunciation = fields.Str(
        required=True,
        description="X-SAMPA phoneme string",
        example='r_0iNtI',
        validate=validate.Length(min=1, max=126)
    )

    url = fields.Str(
        required=True,
        description="The URL for the generate WAV file",
        example=(
            "{}://{}/v0/speak/generated/82fb88cf-914b-41ac-ac1d-6519b2bf181b.wav"
            .format(app.config["SCHEME"],
                    app.config["HOST"])
        )
    )


@app.route("/v0/speak", methods=["POST", "OPTIONS"])
@use_kwargs(SpeakRequest)
@marshal_with(SpeakResponse)
@doc(
    description="Generate WAV file from phoneme string",
    tags=["speak"]
)
@cache.memoize()
def route_post_speak(pronunciation):
    filename = speak_espeak_to_file(pronunciation)

    return jsonify({
        "pronunciation": pronunciation,
        "url": "{}://{}/v0/generated/{}".format(app.config["SCHEME"],
                                                app.config["HOST"],
                                                filename)
    })

docs.register(route_post_speak)


@app.route("/v0/speak", methods=["GET"])
@doc(
    description="Generate WAV file from phoneme string",
    produces=["audio/x-wav"],
    tags=["speak"],
)
@use_kwargs({
    "q": fields.Str(
        required=True,
        description="X-SAMPA phoneme string",
        example='r_0iNtI',
        validate=validate.Length(min=1, max=126)
    ),
}, location="query")
@marshal_with(None)
@cache.memoize()
def route_speak(q):
    return Response(
        response=speak_espeak(q),
        content_type="audio/x-wav"
    )

docs.register(route_speak)


@app.route("/v0/generated/<filename>", methods=["GET", "OPTIONS"])
@marshal_with(None)
@doc(
    produces=["audio/x-wav"],
    tags=["speak"],
)
def route_serve_generated_speech(filename):
    return send_from_directory("generated", filename)

docs.register(route_serve_generated_speech)
