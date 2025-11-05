import json
from dataclasses import dataclass
from typing import Any, Self

from .file import TAG, File
from .text import TextFile


def _merge_values(a: Any, b: Any) -> Any:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return b

    result = {}
    for k, v_a in a.items():
        result[k] = v_a
    for k, v_b in b.items():
        v_a = a.get(k)
        if v_a is None:
            result[k] = v_b
        else:
            result[k] = _merge_values(v_a, v_b)

    return result


@dataclass
class JsonFileProxy:
    file: "JsonFile"
    path: tuple[str, ...]

    def at(self, *path: str) -> Self:
        return JsonFileProxy(self.file, self.path + path)

    def set(self, path: str | tuple[str, ...], value: Any) -> None:
        if isinstance(path, str):
            path = (path,)

        self.file.set(self.path + path, value)

    def tag(self, path: str | tuple[str, ...] = "_tag") -> None:
        self.set(path, TAG)


class JsonFile(File):
    def __init__(self, data: Any = {}) -> None:
        self.data = data

    def at(self, *path: str) -> JsonFileProxy:
        return JsonFileProxy(self, path)

    def get(self, path: str | tuple[str, ...]) -> Any:
        data = self.data
        for part in path:
            data = data[part]
        return data

    def set(self, path: str | tuple[str, ...], value: Any) -> None:
        if isinstance(path, str):
            path = (path,)

        if not path:
            self.data = value
            return

        *parts, last = path

        data = self.data
        for part in parts:
            data = data.setdefault(part, {})
        data[last] = value

    def merge(self, path: str | tuple[str, ...], value: Any) -> None:
        self.set(path, _merge_values(self.get(path), value))

    def tag(self, path: str | tuple[str, ...] = "_tag") -> None:
        self.set(path, TAG)

    def to_text(self) -> TextFile:
        return TextFile(json.dumps(self.data))

    def to_bytes(self) -> bytes:
        return self.to_text().to_bytes()
