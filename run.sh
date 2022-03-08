#!/usr/bin/env bash
set -e

export FLASK_ENV=development
export TIRO_TTS_HOST=localhost:5000
export TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt

[ -f .env.local ] && . .env.local

bazel build :app
bazel test :test_frontend
bazel test :test_frontend_model_dependent
exec bazel-bin/app
