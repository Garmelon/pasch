import hashlib
import json
import random
import string
from pathlib import Path

from rich.console import Console
from rich.markup import escape

from pasch.file.file import File
from pasch.orchestrator import Module, Orchestrator
from pasch.util import fmt_diff, prompt


def random_tmp_path(path: Path) -> Path:
    prefix = "" if path.name.startswith(".") else "."
    suffix = random.sample(string.ascii_letters + string.digits, 6)
    name = f"{prefix}{path.name}.{suffix}~pasch"
    return path.with_name(name)


def atomic_write(path: Path, content: bytes) -> None:
    tmp_path = random_tmp_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_bytes(content)
    tmp_path.rename(path)


def hash_data(data: bytes) -> str:
    m = hashlib.sha256()
    m.update(data)
    return f"sha256-{m.hexdigest()}"


def hash_file(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    return hash_data(data)


def path_to_str(path: Path) -> str:
    return str(path.resolve())


def diff_and_prompt(c: Console, path: Path, new_content_bytes: bytes) -> bool:
    try:
        new_content = new_content_bytes.decode("utf-8")
    except:
        return False

    try:
        old_content = path.read_text(encoding="utf-8")
    except:
        return False

    c.print(fmt_diff(old_content, new_content))
    return prompt("Replace file contents?", default=False)


class FileDb:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict[str, str]:
        try:
            text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}

        data = json.loads(text)
        if type(data) is not dict:
            raise ValueError("file db is not a dict")
        for k, v in data.items():
            if type(v) is not str:
                raise ValueError(f"file db contains non-str hash at key {k!r}")
        return data

    def _save(self, data: dict[str, str]) -> None:
        atomic_write(self._path, json.dumps(data).encode("utf-8"))

    def add_hash(self, path: Path, hash: str) -> None:
        data = self._load()
        data[path_to_str(path)] = hash
        self._save(data)

    def remove_hash(self, path: Path) -> None:
        data = self._load()
        data.pop(path_to_str(path), None)
        self._save(data)

    def verify_hash(self, path: Path, cur_hash: str | None) -> str | None:
        cur_hash = hash_file(path)
        if cur_hash is None:
            return
        known_hash = self._load().get(path_to_str(path))
        if known_hash is None:
            return "File unknown and contents don't match target state."
        if known_hash != cur_hash:
            return "File contents don't match the last known or target state."

    def paths(self) -> list[str]:
        return list(sorted(self._load().keys()))


class Files(Module):
    def __init__(
        self,
        orchestrator: Orchestrator,
        file_db_name: str = "files.json",
        root: Path | None = None,
    ) -> None:
        super().__init__(orchestrator)
        self._files: dict[str, bytes] = {}
        self._file_db = FileDb(self.orchestrator.state_dir / file_db_name)
        self._root = root or Path.home()

    def _read_path(self, path: Path | str) -> Path:
        return self._root / path

    def add(self, path: Path | str, content: File) -> None:
        path = self._read_path(path)
        self._files[path_to_str(path)] = content.to_bytes()

    def realize(self) -> None:
        for path, content in sorted(self._files.items()):
            self._write_file(self._read_path(path), content)

        for path in self._file_db.paths():
            if path not in self._files:
                self._remove_file(self._read_path(path))

    def _write_file(self, path: Path, content: bytes) -> None:
        cur_hash = hash_file(path)
        target_hash = hash_data(content)
        if cur_hash == target_hash:
            return

        relative_path = path.relative_to(self._root, walk_up=True)
        if cur_hash is None:
            self.c.print(f"[bold green]+[/] {escape(str(relative_path))}")
        else:
            self.c.print(f"[bold yellow]~[/] {escape(str(relative_path))}")

        if reason := self._file_db.verify_hash(path, cur_hash):
            self.c.print(f"[red]Error:[/] {escape(reason)}")
            if not diff_and_prompt(self.c, path, content):
                return

        # We want to avoid scenarios where we fail to remember a file we've
        # written. It is better to remember a file with an incorrect hash than
        # to forget it entirely. Thus, we must always update the file db before
        # we write a file.
        self._file_db.add_hash(path, target_hash)
        atomic_write(path, content)

    def _remove_file(self, path: Path) -> None:
        relative_path = path.relative_to(self._root, walk_up=True)
        self.c.print(f"[bold red]-[/] {escape(str(relative_path))}")

        cur_hash = hash_file(path)
        if reason := self._file_db.verify_hash(path, cur_hash):
            self.c.print(f"[red]Error:[/] {escape(reason)}")
            return

        try:
            path.unlink()
        except FileNotFoundError:
            pass
        for parent in path.parents:
            try:
                parent.rmdir()
            except:
                break

        # We want to avoid scenarios where we forget a file without actually
        # removing it. Thus, the db must be updated after the removal.
        self._file_db.remove_hash(path)
