# Copyright 2022 Tiro ehf.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from pathlib import Path

from apispec import APISpec, BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, Response, jsonify, render_template, stream_with_context
from auth.api_key import require_api_key
from flask_apispec import FlaskApiSpec, doc, marshal_with, use_kwargs
from flask_cors import CORS
from webargs.flaskparser import FlaskParser, abort
from werkzeug.middleware.proxy_fix import ProxyFix

from src import schemas, db
from src.config import EnvvarConfig

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
app.config["APISPEC_SWAGGER_UI_URL"] = None
app.config.from_object(EnvvarConfig)

if not app.config["AUTH_DISABLED"]:
    db.setup_db(app)

# Fix access to client remote_addr when running behind proxy
setattr(app, "wsgi_app", ProxyFix(app.wsgi_app))

app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

cors = CORS(app)

# Give everyone access to current_app
app.app_context().push()

# This requires the Flask app context to be initialized. Should probably be refactored a
# bit.
from src.voices import OutputFormat, VoiceManager  # noqa:E402 isort:skip
from src.logging_utils import clean_request

g_synthesizers = VoiceManager.from_pbtxt(Path(app.config["SYNTHESIS_SET_PB"]))


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
    tags=[{"name": "speech", "description": "Synthesize speech from input text"}],
)
docs = FlaskApiSpec(app)


# Use code 400 for invalid requests
FlaskParser.DEFAULT_VALIDATION_STATUS = 400

# Return validation errors as JSON


@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    """Handle request validation errors."""
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])

    json_parameters = None
    query_parameters = None
    if isinstance(messages, dict):
        json_parameters = messages.get("json", {})
        query_parameters = messages.get("query", {})

    message = "Invalid request."
    if not (isinstance(json_parameters, dict) and isinstance(query_parameters, dict)):
        message = "Malformed body or query parameters."
    else:
        parameter_errors = {**json_parameters, **query_parameters}
        if parameter_errors:
            message = "Validation failure for the following fields: {}".format(
                ", ".join(
                    "{}: {}".format(field, err)
                    for field, err in parameter_errors.items()
                )
            )

    if headers:
        return jsonify({"message": message}), err.code, headers
    else:
        return jsonify({"message": message}), err.code


@app.errorhandler(405)
def handle_method_not_allowed(err):
    """Handle authorization errors."""
    response_body = jsonify({"message": "Method not allowed."})
    return response_body, err.code


@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_internal_error(err):
    """Handle unknown/internal server errors."""
    if isinstance(err, Exception):
        app.logger.exception("Hit unhandled internal error", exc_info=err)
    response_body = jsonify(
        {"message": "An unknown conditon has caused a service failure."}
    )

    return response_body, 500


@app.route("/v0/speech", methods=["POST"])
@use_kwargs(schemas.SynthesizeSpeechRequest)
@doc(
    description="Synthesize speech",
    tags=["speech"],
    produces=[
        "audio/mpeg",
        "audio/ogg",
        "application/x-json-stream",
        "audio/x-wav",
        "application/json",
    ],
)
@marshal_with({}, code=200, description="Audio or speech marks content")
@marshal_with(schemas.Error, code=400, description="Bad request")
@marshal_with(schemas.Error, code=500, description="Service error")
@require_api_key
def route_synthesize_speech(**kwargs):
    app.logger.info("Got request: %s", clean_request(kwargs))

    if "Engine" not in kwargs:
        kwargs["Engine"] = "standard"

    output_content_type = "application/x-json-stream"
    voice_id = kwargs["VoiceId"]
    text = kwargs["Text"]
    kwargs["SampleRate"] = kwargs.get("SampleRate", "16000")

    # TODO(rkjaran): error out with a nicer message
    if kwargs["OutputFormat"] == "json" and kwargs.get("SpeechMarkTypes") != ["word"]:
        abort(400)

    if (kwargs["OutputFormat"], kwargs["SampleRate"]) not in g_synthesizers[
        voice_id
    ].properties.supported_output_formats:
        app.logger.info("Client requested unsupported output format")
        abort(400)

    output_content_type = OutputFormat(
        kwargs["OutputFormat"], [kwargs["SampleRate"]]
    ).content_type

    voice = g_synthesizers[voice_id]
    if (
        "LanguageCode" in kwargs
        and voice.properties.language_code != kwargs["LanguageCode"]
    ):

        abort(400)

    try:
        if kwargs.get("TextType") == "ssml":
            return Response(
                stream_with_context(voice.synthesize_from_ssml(text, **kwargs)),
                content_type=output_content_type,
            )
        return Response(
            stream_with_context(voice.synthesize(text, **kwargs)),
            content_type=output_content_type,
        )
    except (NotImplementedError, ValueError) as ex:
        app.logger.warning("Synthesis failed: %s", ex)
        abort(400)


docs.register(route_synthesize_speech)


@app.route("/v0/voices", methods=["GET"])
@use_kwargs(schemas.DescribeVoicesRequest, location="query")
@doc(
    description="Describe/query available voices",
    tags=["speech"],
    produces=["application/json"],
)
@marshal_with(
    schemas.Voice(many=True), code=200, description="List of voices matching query"
)
@marshal_with(schemas.Error, code=400, description="Bad request")
@marshal_with(schemas.Error, code=500, description="Service error")
def route_describe_voices(**kwargs):
    app.logger.info("Got request: %s", clean_request(kwargs))

    def query_filter(elem):
        if "LanguageCode" in kwargs and kwargs["LanguageCode"]:
            return elem["LanguageCode"] == kwargs["LanguageCode"]
        return True

    return jsonify(
        list(
            filter(
                query_filter,
                (
                    {
                        "VoiceId": v[1].properties.voice_id,
                        "Name": v[1].properties.name,
                        "Gender": v[1].properties.gender,
                        "LanguageCode": v[1].properties.language_code,
                        "LanguageName": v[1].properties.language_name,
                        "SupportedEngines": ["standard"],
                    }
                    for v in g_synthesizers.voices()
                ),
            )
        )
    )


docs.register(route_describe_voices)


@app.route("/")
def route_index():
    return render_template("index.dhtml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
