import os
import flask_env

class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    ENV_PREFIX = "TIRO_TTS_"
    HOST = "tts.tiro.is"
    SCHEME = "https"
