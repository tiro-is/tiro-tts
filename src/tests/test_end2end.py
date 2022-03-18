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
import os
from pathlib import Path
from typing import List

import pytest


@pytest.fixture()
def dut_app():
    os.environ["TIRO_TTS_SYNTHESIS_SET_PB"] = "src/tests/synthesis_set_test.pbtxt"
    from src.app import app

    app.config.update(
        {
            "TESTING": True,
        }
    )
    yield app


@pytest.fixture()
def client(dut_app):
    return dut_app.test_client()


@pytest.fixture()
def runner(dut_app):
    return dut_app.test_cli_runner()


def test_describe_voices(client):
    res = client.get("/v0/voices")
    data = res.json
    assert isinstance(data, List)
    assert len(data) > 0
    # The assumption is that we always have Alfur, at least
    assert len([el for el in data if el["VoiceId"] == "Alfur"]) > 0
    assert (
        len(
            [
                el
                for el in data
                if el["VoiceId"] == "Alfur" and el["LanguageCode"] == "is-IS"
            ]
        )
        > 0
    )
    assert (
        len([el for el in data if el["VoiceId"] == "Alfur" and el["Gender"] == "Male"])
        > 0
    )


def test_synthesize_pcm_native_freq_sanity(client):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": "Hæ! Ég heiti Gervimaður Finnland, en þú?",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0
