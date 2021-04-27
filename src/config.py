import os
import flask_env


class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    ENV_PREFIX = "TIRO_TTS_"
    HOST = "tts.tiro.is"
    SCHEME = "https"
    CACHE_TYPE = "filesystem"
    CACHE_DIR = "generated"
    CACHE_DEFAULT_TIMEOUT = 60 * 60 * 24 * 2

    # For acess to Polly
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None
    AWS_REGION = "eu-west-1"

    # For FastSpeech2
    MELGAN_VOCODER_PATH = None
    FASTSPEECH_MODEL_PATH = None
    SEQUITUR_MODEL_PATH = None
