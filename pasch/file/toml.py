from dataclasses import dataclass
from typing import Any, Self

import toml

from .file import File
from .text import TextFile


@dataclass
class TomlFileProxy:
    file: "TomlFile"
    path: tuple[str, ...]

    def at(self, *path: str) -> Self:
        return TomlFileProxy(self.file, self.path + path)

    def set(self, value: Any) -> None:
        if not self.path:
            self.file.set(value)

        data = self.file.data
        *parts, last = self.path
        for part in parts:
            data = data.setdefault(part, {})
        data[last] = value


class TomlFile(File):
    def __init__(self, data: Any = {}) -> None:
        self.data = data

    def at(self, *path: str) -> TomlFileProxy:
        return TomlFileProxy(self, path)

    def set(self, value: Any) -> None:
        self.data = value

    def to_text(self) -> TextFile:
        file = TextFile()
        file.tag(comment="#")
        file.append(toml.dumps(self.data))
        return file

    def to_bytes(self) -> bytes:
        return self.to_text().to_bytes()
