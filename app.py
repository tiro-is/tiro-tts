import os
import uuid
from copy import deepcopy
import math
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from webargs import fields
from flask_apispec import use_kwargs, marshal_with, FlaskApiSpec, doc
from flask_caching import Cache
from marshmallow import validate, Schema
from apispec import APISpec, BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from typing import Dict, List
import re
import subprocess

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
app.config["APISPEC_SWAGGER_UI_URL"] = "/v0/docs/"
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 60*60*24*2

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
    host="tts.tiro.is",
    openapi_version="2.0",
    plugins=[MarshmallowPlugin(), DisableOptionsOperationPlugin()],
)
docs = FlaskApiSpec(app)


def speak_espeak(phoneme_string):
    wav = subprocess.check_output(
        "echo '[[{}]]' | espeak-ng -v icelandic --stdout", shell=True
    )
    return wav

def speak_espeak_to_file(phoneme_string) -> str:
    filename = "{}.wav".format(uuid.uuid4())

    wav = subprocess.check_output(
        "echo '[[{}]]' | espeak-ng -v icelandic -w generated/".format(
            phoneme_string, filename
        ),
        shell=True
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
        example="https://tts.tiro.is/v0/speak/generated/"
    )


@app.route("/v0/speak", methods=["POST", "OPTIONS"])
@use_kwargs(SpeakRequest, location="json")
@marshal_with(SpeakResponse)
@doc(description="Generate WAV file from phoneme string")
def route_post_speak(pronunciation):
    filename = speak_espeak_to_file(pronunciation)
    return json.dumps({
        "pronunciation": pronunciation,
        "url": "https://tts.tiro.is/v0/generated/{}".format(filename)
    })

docs.register(route_post_speak)


@app.route("/v0/speak", methods=["GET"])
@doc(description="Generate WAV file from phoneme string")
@use_kwargs({
    "q": fields.Str(
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


@app.route("/v0/generated/<filename:str>", methods=["GET", "OPTIONS"])
def route_serve_generated_speech(filename):
    return send_from_directory("generated", filename)

docs.register(route_serve_generated_speech)



# @app.route("/pron", methods=["POST", "OPTIONS"])
# @doc(description="Output pronunciation list of words")
# @use_kwargs({
#     "words": fields.List(fields.Str(), example=["bandabrandur"]),
#     "t": fields.Str(
#         description="Output type. Valid values are `tsv` and `json`",
#         example='json',
#         validate=validate.OneOf(['json', 'tsv']),
#     ),
#     "max_variants_number": fields.Int(
#         description="Maximum number of pronunciation variants generated with "
#         "G2P. Default is 4",
#         validate=validate.Range(min=0, max=20),
#         example=4,
#     ),
#     "total_variants_mass": fields.Float(
#         description="Generate pronuncation variants with G2P until this "
#         "probability mass or until number reaches `max_variants_number`",
#         validate=validate.Range(min=0.0, max=1.0),
#         example=0.9
#     ),
#     "language_code": fields.Str(
#         description="Language code for words",
#         validate=validate.OneOf(models.keys()),
#         missing='is-IS'
#     ),
# })
# @marshal_with(None)
# @cache.memoize()
# def route_pronounce_many(words, max_variants_number=4,
#                          total_variants_mass=0.9, t='json', language_code='is-IS'):
#     pron = pronounce(
#         words,
#         max_variants_number=max_variants_number,
#         variants_mass=total_variants_mass,
#         language_code=language_code
#     )
#     if t and t == "tsv":
#         return Response(response=pron_to_tsv(pron),
#                         status=200,
#                         content_type="text/tab-separated-values")
#     return jsonify(list(pron))

# docs.register(route_pronounce_many)
