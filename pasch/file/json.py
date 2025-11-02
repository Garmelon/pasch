from typing import Self
import json
from dataclasses import dataclass
from typing import Any

from .file import TAG, File
from .text import TextFile


@dataclass
class JsonFileProxy:
    file: "JsonFile"
    path: tuple[str, ...]

    def at(self, *path: str) -> Self:
        return JsonFileProxy(self.file, self.path + path)

    def set(self, value: Any) -> None:
        if not self.path:
            self.file.set(value)

        data = self.file.data
        *parts, last = self.path
        for part in parts:
            data = data[part]
        data[last] = value

    def tag_here(self, tag: str = TAG) -> None:
        self.set(tag)


class JsonFile(File):
    def __init__(self, data: Any = {}) -> None:
        self.data = data

    def at(self, *path: str) -> JsonFileProxy:
        return JsonFileProxy(self, path)

    def set(self, value: Any) -> None:
        self.data = value

    def tag(self, tag: str = TAG, key: str | list[str] = "_tag") -> None:
        if isinstance(key, str):
            self.at(key).tag_here(tag=tag)
        self.at(*key).tag_here(tag=tag)

    def to_text(self) -> TextFile:
        return TextFile(json.dumps(self.data))

    def to_bytes(self) -> bytes:
        return self.to_text().to_bytes()
