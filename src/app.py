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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from flask import (
    Flask,
    jsonify,
    render_template,
    Response,
    stream_with_context,
)
from flask_cors import CORS
from webargs.flaskparser import FlaskParser, abort
from flask_apispec import use_kwargs, marshal_with, FlaskApiSpec, doc
from flask_caching import Cache
from apispec import APISpec, BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from config import EnvvarConfig
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
app.config["APISPEC_SWAGGER_UI_URL"] = None
app.config.from_object(EnvvarConfig)

# Fix access to client remote_addr when running behind proxy
setattr(app, "wsgi_app", ProxyFix(app.wsgi_app))

app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
app.config["CACHE_NO_NULL_WARNING"] = True

cors = CORS(app)
cache = Cache(app)

# Give everyone access to current_app
app.app_context().push()

from voices import OutputFormat, VoiceManager
import schemas

g_synthesizers = VoiceManager()


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
        {"name": "speech", "description": "Synthesize speech from input text"},
    ],
)
docs = FlaskApiSpec(app)


# Use code 400 for invalid requests
FlaskParser.DEFAULT_VALIDATION_STATUS = 400

# Return validation errors as JSON
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


@app.route("/v0/speech", methods=["POST"])
@use_kwargs(schemas.SynthesizeSpeechRequest)
@doc(
    description="Synthesize speech",
    tags=["speech"],
    produces=["audio/mpeg", "audio/ogg", "application/x-json-stream", "audio/x-wav"],
)
@cache.memoize()
def route_synthesize_speech(**kwargs):
    app.logger.info("Got request: %s", kwargs)

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
def route_describe_voices(**kwargs):
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
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    app.run()
