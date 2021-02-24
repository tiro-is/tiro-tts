import os
import flask_env

class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    ENV_PREFIX = "TIRO_TTS_"
    HOST = "tts.tiro.is"
    SCHEME = "https"
    CACHE_TYPE = "filesystem"
    CACHE_DIR = "generated"
    CACHE_DEFAULT_TIMEOUT = 60 * 60 * 24 * 2
