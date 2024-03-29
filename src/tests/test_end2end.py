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
import json
import os
from typing import Dict, List

import pytest


@pytest.fixture(scope="session")
def dut_app():
    os.environ["TIRO_TTS_SYNTHESIS_SET_PB"] = "src/tests/synthesis_set_test.pbtxt"

    from src import init_app

    app = init_app()

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


@pytest.fixture(params=["'", '"'])
def quote(request):
    return request.param


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


def test_synthesize_speech_marks_sanity(client):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "json",
            "SpeechMarkTypes": ["word"],
            "Text": "Hæ! Ég heiti Gervimaður Finnland, en þú?",
            "VoiceId": "Alfur",
        },
    )

    data = res.get_data(as_text=True).split("\n")
    marks = [json.loads(line) for line in data if line.strip()]
    last_time = 0
    for (mark, original_word,) in zip(
        [mark for mark in marks if mark["type"] == "word"],
        ["Hæ", "Ég", "heiti", "Gervimaður", "Finnland", "en", "þú"],
    ):
        assert mark["time"] >= last_time
        last_time = mark["time"]
        assert mark["value"] == original_word


def test_synthesize_ssml_sanity(client):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": "<speak>Hæ! Ég heiti Gervimaður Finnland, en þú?</speak>",
            "TextType": "ssml",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0


def test_synthesize_ssml_phoneme_sanity(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": f"<speak>Hæ! Ég <phoneme alphabet={quote}x-sampa{quote} ph={quote}hei:tI{quote}>heiti</phoneme> Gervimaður Finnland, en þú?</speak>",
            "TextType": "ssml",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0


def test_synthesize_ssml_prosody_sanity_01(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": f"<speak>Við notum <prosody volume={quote}x-loud{quote}>123 vafrakökur á þessari vefsíðu ehf hehehe</prosody></speak>",
            "TextType": "ssml",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0


def test_synthesize_ssml_prosody_sanity_02(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": f"<speak>Við notum <prosody volume={quote}x-loud{quote} pitch={quote}high{quote} rate={quote}140%{quote}>123 vafrakökur á þessari vefsíðu ehf hehehe</prosody></speak>",
            "TextType": "ssml",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0


def test_synthesize_ssml_say_as_sanity_01(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": f"<speak>Við notum <say-as interpret-as={quote}digits{quote}>123</say-as> vafrakökur á þessari vefsíðu ehf hehehe</speak>",
            "TextType": "ssml",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0


def test_synthesize_ssml_sub_sanity_01(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "pcm",
            "SampleRate": "22050",
            "Text": f"<speak>Við notum <sub alias={quote}rosa margar{quote}>123</sub> vafrakökur á þessari vefsíðu ehf hehehe</speak>",
            "TextType": "ssml",
            "VoiceId": "Alfur",
        },
    )

    pcm_data = res.get_data(as_text=False)
    # The response contains some reasonable number of bytes
    assert len(pcm_data) > 4000
    # And each sample is two bytes
    assert len(pcm_data) % 2 == 0


def test_speechmarks_fastspeech(client):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "json",
            "SampleRate": "22050",
            "Text": "Honum var sagt að grænmetið kostaði kr. 22000 og þótti það ekki mikið.",
            "TextType": "text",
            "SpeechMarkTypes": ["word"],
            "VoiceId": "Alfur",
        },
    )

    data = res.get_data(as_text=True).split("\n")
    marks = [json.loads(line) for line in data if line.strip()]
    marks_filtered = [
        {"start": mark["start"], "end": mark["end"], "value": mark["value"]}
        for mark in marks
    ]

    marks_expected: List[Dict] = [
        {"start": 0, "end": 5, "value": "Honum"},
        {"start": 6, "end": 9, "value": "var"},
        {"start": 10, "end": 14, "value": "sagt"},
        {"start": 15, "end": 18, "value": "að"},
        {"start": 19, "end": 30, "value": "grænmetið"},
        {"start": 31, "end": 39, "value": "kostaði"},
        {"start": 40, "end": 43, "value": "kr."},
        {"start": 44, "end": 49, "value": "22000"},
        {"start": 50, "end": 52, "value": "og"},
        {"start": 53, "end": 60, "value": "þótti"},
        {"start": 61, "end": 66, "value": "það"},
        {"start": 67, "end": 71, "value": "ekki"},
        {"start": 72, "end": 78, "value": "mikið"},
    ]

    assert len(marks_filtered) == len(marks_expected)
    for original_mark, expected_mark in zip(marks_filtered, marks_expected):
        assert original_mark == expected_mark


def test_ssml_speechmarks_fastspeech_01(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "json",
            "SampleRate": "22050",
            "Text": f"<speak>Hæ! Ég <phoneme alphabet={quote}x-sampa{quote} ph={quote}hei:tI{quote}>heiti</phoneme> Gervimaður Finnland & er hestur. En þú?</speak>",
            "TextType": "ssml",
            "SpeechMarkTypes": ["word"],
            "VoiceId": "Alfur",
        },
    )

    data = res.get_data(as_text=True).split("\n")
    marks = [json.loads(line) for line in data if line.strip()]
    marks_filtered = [
        {"start": mark["start"], "end": mark["end"], "value": mark["value"]}
        for mark in marks
    ]

    marks_expected: List[Dict] = [
        {"start": 7, "end": 10, "value": "Hæ"},
        {"start": 12, "end": 15, "value": "Ég"},
        {"start": 56, "end": 61, "value": "heiti"},
        {"start": 72, "end": 83, "value": "Gervimaður"},
        {"start": 84, "end": 92, "value": "Finnland"},
        {"start": 95, "end": 97, "value": "er"},
        {"start": 98, "end": 104, "value": "hestur"},
        {"start": 106, "end": 108, "value": "En"},
        {"start": 109, "end": 113, "value": "þú"},
    ]

    assert len(marks_filtered) == len(marks_expected)
    for original_mark, expected_mark in zip(marks_filtered, marks_expected):
        assert original_mark == expected_mark


def test_ssml_speechmarks_fastspeech_02(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "json",
            "SampleRate": "22050",
            "Text": f"<speak>Alls náðu 22 konur að sigla með <phoneme alphabet={quote}x-sampa{quote} ph={quote}t_hai:t_hanIk{quote}>Titanic halló. Hæ </phoneme> og borguðu fyrir það 57006 kr.</speak>",
            "TextType": "ssml",
            "SpeechMarkTypes": ["word"],
            "VoiceId": "Alfur",
        },
    )

    data = res.get_data(as_text=True).split("\n")
    marks = [json.loads(line) for line in data if line.strip()]
    marks_filtered = [
        {"start": mark["start"], "end": mark["end"], "value": mark["value"]}
        for mark in marks
    ]

    marks_expected: List[Dict] = [
        {"start": 7, "end": 11, "value": "Alls"},
        {"start": 12, "end": 18, "value": "náðu"},
        {"start": 19, "end": 21, "value": "22"},
        {"start": 22, "end": 27, "value": "konur"},
        {"start": 28, "end": 31, "value": "að"},
        {"start": 32, "end": 37, "value": "sigla"},
        {"start": 38, "end": 42, "value": "með"},
        {"start": 90, "end": 109, "value": "Titanic halló. Hæ "},
        {"start": 121, "end": 123, "value": "og"},
        {"start": 124, "end": 132, "value": "borguðu"},
        {"start": 133, "end": 138, "value": "fyrir"},
        {"start": 139, "end": 144, "value": "það"},
        {"start": 145, "end": 150, "value": "57006"},
        {"start": 151, "end": 154, "value": "kr."},
    ]

    assert len(marks_filtered) == len(marks_expected)
    for original_mark, expected_mark in zip(marks_filtered, marks_expected):
        assert original_mark == expected_mark


def test_ssml_speechmarks_fastspeech_03(client, quote):
    res = client.post(
        "/v0/speech",
        json={
            "OutputFormat": "json",
            "SampleRate": "22050",
            "Text": f"<speak><phoneme alphabet={quote}x-sampa{quote} ph={quote}a:fI{quote}>Afi</phoneme> minn fór á honum <phoneme alphabet={quote}x-sampa{quote} ph={quote}t9i:D{quote}>rauð</phoneme></speak>",
            "TextType": "ssml",
            "SpeechMarkTypes": ["word"],
            "VoiceId": "Alfur",
        },
    )

    data = res.get_data(as_text=True).split("\n")
    marks = [json.loads(line) for line in data if line.strip()]
    marks_filtered = [
        {"start": mark["start"], "end": mark["end"], "value": mark["value"]}
        for mark in marks
    ]

    marks_expected: List[Dict] = [
        {"start": 45, "end": 48, "value": "Afi"},
        {"start": 59, "end": 63, "value": "minn"},
        {"start": 64, "end": 68, "value": "fór"},
        {"start": 69, "end": 71, "value": "á"},
        {"start": 72, "end": 77, "value": "honum"},
        {"start": 117, "end": 122, "value": "rauð"},
    ]

    assert len(marks_filtered) == len(marks_expected)
    for original_mark, expected_mark in zip(marks_filtered, marks_expected):
        assert original_mark == expected_mark
