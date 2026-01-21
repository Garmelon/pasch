from rich.markup import escape

from pasch.file.json import JsonFile
from pasch.modules.files import Files
from pasch.modules.pacman import Pacman
from pasch.orchestrator import Module, Orchestrator
from pasch.util import run_capture, run_execute


class Vscode(Module):
    def __init__(
        self,
        orchestrator: Orchestrator,
        files: Files,
        pacman: Pacman,
    ) -> None:
        super().__init__(orchestrator)
        self._files = files
        self._pacman = pacman

        self.microsoft = False
        self.disable_telemetry = True

        self.extensions: set[str] = set()
        self.settings = JsonFile()

    def install(self, *extensions: str) -> None:
        self.extensions.update(extensions)

    def configure(self) -> None:
        self.settings.tag()

        if self.disable_telemetry:
            self.settings.set("telemetry.editStats.enabled", False)
            self.settings.set("telemetry.feedback.enabled", False)
            self.settings.set("telemetry.telemetryLevel", "off")
            self.settings.set("update.mode", "none")

        if self.microsoft:
            self._pacman.install("visual-studio-code-bin")
            self._files.add(".config/Code/User/settings.json", self.settings)
        else:
            self._pacman.install("code")
            self._files.add(".config/Code - OSS/User/settings.json", self.settings)

    def execute(self) -> None:
        installed = set(run_capture("code", "--list-extensions").splitlines())

        to_install = self.extensions - installed
        to_uninstall = installed - self.extensions

        for package in sorted(to_install):
            self.c.print(f"[bold green]+[/] {escape(package)}")
        for package in sorted(to_uninstall):
            self.c.print(f"[bold red]-[/] {escape(package)}")

        for extension in sorted(to_install):
            run_execute("code", "--install-extension", extension)

        for extension in sorted(to_uninstall):
            run_execute("code", "--uninstall-extension", extension)
