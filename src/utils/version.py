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
import ast
import hashlib
import inspect
from abc import ABC, abstractmethod
from typing import Any, Optional, Type


class VersionedThing(ABC):
    @property
    @abstractmethod
    def version_hash(self) -> str:
        """A stable version hash

        The hash includes anything that might effect the output of the main
        entrypoint. E.g. for NormalizerBase that would be normalize and the hash would
        include the implementation[1], any models used and versioning info for any RPC
        used.

        [1] This implies that an implementation of this should probably use the
        `inspect` and `ast` modules from the Python stdlib.

        """
        ...


def hash_from_impl(cls: Type[Any], additional: Optional[str] = None) -> str:
    return hashlib.sha1(
        (additional if additional else "").encode()
        + ast.dump(ast.parse(inspect.getsource(cls))).encode()
    ).hexdigest()
