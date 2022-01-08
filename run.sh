#!/bin/sh -e
export FLASK_ENV=development
export TIRO_TTS_HOST=localhost:5000
export TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt
bazel build :app
bazel test :unit_test
exec bazel-bin/app
