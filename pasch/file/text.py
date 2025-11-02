from .binary import BinaryFile
from .file import TAG, File


class TextFile(File):
    def __init__(self, data: str = "") -> None:
        self.data = data

    def prepend(self, line: str, newline: bool = True) -> None:
        if newline:
            line = f"{line}\n"
        self.data = line + self.data

    def append(self, line: str, newline: bool = True) -> None:
        if newline:
            line = f"{line}\n"
        self.data = self.data + line

    def tag(
        self,
        tag: str = TAG,
        comment: str | None = None,
        newline: bool = True,
        prepend: bool = True,
    ) -> None:
        if comment is not None:
            tag = f"{comment} {tag}"
        if prepend:
            self.prepend(tag, newline=newline)
        else:
            self.append(tag, newline=newline)

    def to_binary(self) -> BinaryFile:
        return BinaryFile(self.data.encode("utf-8"))

    def to_bytes(self) -> bytes:
        return self.to_binary().to_bytes()
