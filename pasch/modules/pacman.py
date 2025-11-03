from dataclasses import dataclass, field
from subprocess import CalledProcessError

from rich.markup import escape

from pasch.orchestrator import Module, Orchestrator
from pasch.util import run_capture, run_execute


@dataclass
class PacmanPackage:
    name: str
    exclude: set[str] = field(default_factory=set)


class Pacman(Module):
    def __init__(self, orchestrator: Orchestrator) -> None:
        super().__init__(orchestrator)
        self.binary: str = "pacman"
        self.packages: set[str] = set()
        self.excluded: dict[str, set[str]] = {}

    def install(self, *packages: str) -> None:
        self.packages.update(packages)

    def exclude(self, group: str, *packages: str) -> None:
        self.excluded.setdefault(group, set()).update(packages)

    def realize(self) -> None:
        groups = self._get_groups()

        installed = self._get_explicitly_installed_packages()
        target = self._resolve_packages(groups, self.packages)

        to_install = target - installed
        to_uninstall = installed - target

        for package in sorted(to_install):
            self.c.print(f"[bold green]+[/] {escape(package)}")
        for package in sorted(to_uninstall):
            self.c.print(f"[bold red]-[/] {escape(package)}")

        self._install_packages(to_install)
        self._uninstall_packages(to_uninstall)

    def _pacman_capture(self, *args: str) -> str:
        return run_capture(self.binary, *args)

    def _pacman_execute(self, *args: str) -> None:
        if self.binary == "paru":
            run_execute(self.binary, *args)  # Calls sudo itself
        else:
            run_execute("sudo", self.binary, *args)

    def _get_explicitly_installed_packages(self) -> set[str]:
        return set(self._pacman_capture("-Qqe").splitlines())

    def _get_groups(self) -> dict[str, set[str]]:
        groups = {}
        for line in self._pacman_capture("-Sgg").splitlines():
            group, package = line.split(" ", maxsplit=1)
            groups.setdefault(group, set()).add(package)
        return groups

    def _resolve_packages(
        self,
        groups: dict[str, set[str]],
        packages: set[str],
    ) -> set[str]:
        result = set()
        for package in packages:
            result.update(self._resolve_package(groups, package))
        return result

    def _resolve_package(self, groups: dict[str, set[str]], package: str) -> set[str]:
        packages = groups.get(package)
        if packages is None:
            return {package}
        packages = packages - self.excluded.get(package, set())
        return self._resolve_packages(groups, packages)

    def _install_packages(self, packages: set[str]) -> None:
        if self.orchestrator.dry_run:
            return

        if packages:
            self._pacman_execute("-S", "--needed", *sorted(packages))
            self._pacman_execute("-D", "--asexplicit", *sorted(packages))

    def _uninstall_packages(self, packages: set[str]) -> None:
        if self.orchestrator.dry_run:
            return

        if packages:
            self._pacman_execute("-D", "--asdeps", *sorted(packages))

        try:
            to_remove = self._pacman_capture("-Qqdt").splitlines()
        except CalledProcessError:
            return  # pacman returns nonzero exit code if the query is empty

        if to_remove:
            self._pacman_execute("-Rsn", *to_remove)
