from .file import File


class BinaryFile(File):
    def __init__(self, data: bytes) -> None:
        self.data = data

    def to_bytes(self) -> bytes:
        return self.data
