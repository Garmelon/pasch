from dataclasses import dataclass
from typing import Any, Self

import toml

from .file import File
from .json import JsonFile
from .text import TextFile


@dataclass
class TomlFileProxy:
    file: "TomlFile"
    path: tuple[str, ...]

    def at(self, *path: str) -> Self:
        return TomlFileProxy(self.file, self.path + path)

    def set(self, path: str | tuple[str, ...], value: Any) -> None:
        if isinstance(path, str):
            path = (path,)

        self.file.set(self.path + path, value)


class TomlFile(File):
    def __init__(self, data: Any = {}) -> None:
        self.json = JsonFile(data)

    def at(self, *path: str) -> TomlFileProxy:
        return TomlFileProxy(self, path)

    def get(self, path: str | tuple[str, ...]) -> Any:
        return self.json.get(path)

    def set(self, path: str | tuple[str, ...], value: Any) -> None:
        self.json.set(path, value)

    def merge(self, path: str | tuple[str, ...], value: Any) -> None:
        self.json.merge(path, value)

    def to_text(self) -> TextFile:
        file = TextFile()
        file.tag(comment="#")
        file.append(toml.dumps(self.json.data), newline=False)
        return file

    def to_bytes(self) -> bytes:
        return self.to_text().to_bytes()
