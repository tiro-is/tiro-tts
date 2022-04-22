#!/usr/bin/env bash
set -e

export FLASK_ENV=development
export TIRO_TTS_HOST=localhost:5000
export TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt

[ -f .env.local ] && . .env.local

bazel build :main
bazel test :* -- -//:pip_compile_test
exec bazel-bin/main
