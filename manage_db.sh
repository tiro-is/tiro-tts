#!/bin/bash
set -e

TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt bazel-bin/repl ./manage_db.py $@
