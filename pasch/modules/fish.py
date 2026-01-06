import os
from dataclasses import dataclass

from pasch.file.text import TextFile
from pasch.modules.files import Files
from pasch.modules.pacman import Pacman
from pasch.orchestrator import Module, Orchestrator
from pasch.util import prompt, run_execute


def escape(s: str) -> str:
    # The only meaningful escape sequences in single quotes are `\'`, which
    # escapes a single quote and `\\`, which escapes the backslash symbol.
    ESCAPES = {"'": "\\'", "\\": "\\\\"}
    escaped = "".join(ESCAPES.get(c, c) for c in s)
    return f"'{escaped}'"


@dataclass
class Raw:
    string: str


type FishStr = str | Raw


def fescape(s: FishStr) -> str:
    if isinstance(s, Raw):
        return s.string
    return escape(s)


class Fish(Module):
    def __init__(
        self,
        orchestrator: Orchestrator,
        files: Files,
        pacman: Pacman,
    ) -> None:
        super().__init__(orchestrator)
        self._files = files
        self._pacman = pacman

        self.path: list[FishStr] = []
        self.abbrs: dict[str, FishStr] = {}
        self.env_vars: dict[str, FishStr] = {}

        self.commands: list[str] = []
        self.interactive_commands: list[str] = []

    def add_to_path(self, value: FishStr) -> None:
        self.path.append(value)

    def add_abbr(self, name: str, replacement: FishStr) -> None:
        self.abbrs[name] = replacement

    def add_env_var(self, name: str, value: FishStr) -> None:
        self.env_vars[name] = value

    def add_command(self, command: str) -> None:
        self.commands.append(command)

    def add_interactive(self, command: str) -> None:
        self.interactive_commands.append(command)

    def configure(self) -> None:
        file = TextFile()
        file.tag(comment="#")

        # Commands set by the user should always appear after generated commands
        commands = self.commands
        interactive_commands = self.interactive_commands
        self.commands = []
        self.interactive_commands = []

        for segment in self.path:
            self.add_command(f"fish_add_path --path --append {fescape(segment)}")
        for name, replacement in sorted(self.abbrs.items()):
            self.add_interactive(f"abbr {escape(name)} {fescape(replacement)}")
        for name, value in sorted(self.env_vars.items()):
            self.add_command(f"set -gx {escape(name)} {fescape(value)}")

        self.commands.extend(commands)
        self.interactive_commands.extend(interactive_commands)

        if self.commands:
            file.append("")
            for command in self.commands:
                file.append(command)
        if self.interactive_commands:
            file.append("")
            file.append("if status is-interactive")
            for command in self.interactive_commands:
                file.append(f"  {command}")
            file.append("end")

        self._files.add(".config/fish/config.fish", file)
        self._pacman.install("fish")

    def execute(self) -> None:
        shell = os.environ.get("SHELL")
        if shell == "/usr/bin/fish":
            return
        fix = prompt("Your shell is not fish. Set it to fish?", default=False)
        if not fix:
            return
        run_execute("sudo", "usermod", "--shell", "/usr/bin/fish", self.o.user)
