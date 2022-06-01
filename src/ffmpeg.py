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
import shutil
import subprocess as sp
from dataclasses import dataclass
from typing import List, Literal, Optional


def _find_ffmpeg() -> str:
    path = shutil.which("external/ffmpeg/ffmpeg")
    if path:
        return path
    path = shutil.which("ffmpeg")
    if path:
        return path
    raise RuntimeError("ffmpeg not found")


_FFMPEG_ARGS = [
    _find_ffmpeg(),
    "-hide_banner",
    "-loglevel",
    "error",
]


@dataclass
class Prosody:
    rate: Optional[float] = None
    pitch: Optional[float] = None
    volume: Optional[float] = None


def _input_args(
    src_sample_rate: str = "22050",
    src_fmt: str = "s16le",
    *,
    prosody: Optional[Prosody] = None,
) -> List[str]:
    return [
        "-ac",
        "1",
        "-ar",
        src_sample_rate,
        "-f",
        src_fmt,
        "-i",
        "-",
    ] + _filter_args(int(src_sample_rate), prosody=prosody)


def _filter_args(
    src_sample_rate: int,
    *,
    prosody: Optional[Prosody] = None,
) -> List[str]:
    """Construct ffmpeg audio filter arguments for prosody

    Args:
      src_sample_rate: the sample rate of the source audio
      rate, pitch, volume: floats that specify the gain for each property, i.e. 1.0
        being the default.

    Returns:
      list of arguments to be added to a ffmpeg argument list

    """
    if not prosody:
        return []

    if any(x <= 0.0 for x in (prosody.rate, prosody.pitch) if x is not None):
        raise ValueError("Negative values not allowed for pitch or rate.")

    filter_args = []

    if prosody.pitch:
        filter_args.extend(
            [f"asetrate={prosody.pitch * src_sample_rate}", f"atempo={1/prosody.pitch}"]
        )

    if prosody.rate:
        filter_args.extend([f"atempo={prosody.rate if prosody.rate >= 0.5 else 0.5}"])

    if prosody.volume:
        filter_args.extend([f"volume={prosody.volume}dB"])

    return (
        [
            "-filter:a",
            ",".join(filter_args),
        ]
        if filter_args
        else []
    )


def to_format(
    *,
    out_format: Literal["ogg_vorbis", "mp3", "pcm"],
    audio_content: bytes,
    sample_rate: str,
    src_sample_rate: str = "22050",
    src_fmt: str = "s16le",
    prosody: Optional[Prosody] = None,
) -> bytes:
    input_args = _input_args(
        src_fmt=src_fmt, src_sample_rate=src_sample_rate, prosody=prosody
    )
    if out_format == "ogg_vorbis":
        return to_ogg_vorbis(audio_content, sample_rate, input_args)
    elif out_format == "mp3":
        return to_mp3(audio_content, sample_rate, input_args)
    elif out_format == "pcm":
        return to_s16le(audio_content, sample_rate, input_args)
    else:
        raise ValueError("Invalid output format")


def to_s16le(
    audio_content: bytes,
    sample_rate: str,
    input_args: List[str],
) -> bytes:
    """Convert audio to Ogg Vorbis (using ffmpeg)

    Args:
      audio_content  Any audio content (with headers) that the available ffmpeg binary
                     can decode
      sample_rate Output sample rate in Hertz

    Returns:
      Signed linear 16 bit little endian PCM encoded audio content

    """
    content = sp.check_output(
        _FFMPEG_ARGS
        + input_args
        + [
            "-ar",
            sample_rate,
            "-f",
            "s16le",
            "-",
        ],
        input=audio_content,
    )
    return content


# TODO(rkjaran): Implement these using generators/streams to decrease latency
def to_ogg_vorbis(
    audio_content: bytes,
    sample_rate: str,
    input_args: List[str],
) -> bytes:
    """Convert audio to Ogg Vorbis (using ffmpeg)

    Args:
      audio_content  Any audio content (with headers) that the available ffmpeg binary
                     can decode
      sample_rate Output sample rate in Hertz

    Returns:
      Ogg Vorbis encoded audio content

    """
    content = sp.check_output(
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
    return content


def to_mp3(
    audio_content: bytes,
    sample_rate: str,
    input_args: List[str],
) -> bytes:
    """Convert audio to MP3 (using ffmpeg)

    Args:
      audio_content  Any audio content (with headers) that the available ffmpeg binary
                     can decode
      sample_rate Output sample rate in Hertz

    Returns:
      MP3 encoded audio content

    """
    content = sp.check_output(
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
    return content
