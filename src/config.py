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
import flask_env


class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    ENV_PREFIX = "TIRO_TTS_"
    HOST = "tts.tiro.is"
    SCHEME = "https"

    # For acess to Polly
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None
    AWS_REGION = "eu-west-1"

    SYNTHESIS_SET_PB = "conf/synthesis_set.pbtxt"

    # Features flags

    # Strip the text content from all logged requests
    STRIP_TEXT = True

    # Enable to use ffmpeg executable to encode ogg_vorbis/mp3
    USE_FFMPEG = True

    # Use this variable to enable or disable auth(orization|entication)
    AUTH_DISABLED = True
