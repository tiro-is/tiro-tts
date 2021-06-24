# Copyright 2021 Tiro ehf.
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
import subprocess as sp

_FFMPEG_ARGS = [
    "ffmpeg",
    "-hide_banner",
    "-loglevel",
    "error",
]


# TODO(rkjaran): Implement these using generators/streams to decrease latency
def to_ogg_vorbis(
    audio_content: bytes,
    sample_rate: str,
    src_sample_rate: str = "22050",
    src_fmt: str = "s16le",
) -> bytes:
    """Convert audio to Ogg Vorbis (using ffmpeg)

    Args:
      audio_content  Any audio content (with headers) that the available ffmpeg binary
                     can decode
      sample_rate Output sample rate in Hertz

    Returns:
      Ogg Vorbis encoded audio content

    """
    input_args = [
        "-ac",
        "1",
        "-ar",
        src_sample_rate,
        "-f",
        src_fmt,
        "-i",
        "-",
    ]
    ogg_vorbis_content = sp.check_output(
        _FFMPEG_ARGS
        + input_args
        + [
            "-acodec",
            "libvorbis",
            "-ar",
            sample_rate,
            "-f",
            "ogg",
            "-",
        ],
        input=audio_content,
    )
    return ogg_vorbis_content


def to_mp3(
    audio_content: bytes,
    sample_rate: str,
    src_sample_rate: str = "22050",
    src_fmt: str = "s16le",
) -> bytes:
    """Convert audio to MP3 (using ffmpeg)

    Args:
      audio_content  Any audio content (with headers) that the available ffmpeg binary
                     can decode
      sample_rate Output sample rate in Hertz

    Returns:
      Ogg Vorbis encoded audio content

    """
    input_args = [
        "-ac",
        "1",
        "-ar",
        src_sample_rate,
        "-f",
        src_fmt,
        "-i",
        "-",
    ]
    mp3_content = sp.check_output(
        _FFMPEG_ARGS
        + input_args
        + [
            "-ar",
            sample_rate,
            "-f",
            "mp3",
            "-",
        ],
        input=audio_content,
    )
    return mp3_content
