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
import sys

import numpy as np
import resampy


def wavarray_to_pcm(
    array: np.ndarray, src_sample_rate: int = 22050, dst_sample_rate: int = 22050
) -> bytes:
    """Convert a NDArray (int16) to a PCM byte chunk, resampling if necessary."""

    def to_pcm_bytes(array1d):
        return array1d.view("b").data.tobytes()

    if sys.byteorder == "big":
        array.byteswap()

    orig_samples = array.ravel()
    if src_sample_rate == dst_sample_rate:
        return to_pcm_bytes(orig_samples)
    return to_pcm_bytes(
        resampy.resample(orig_samples, src_sample_rate, dst_sample_rate)
    )
