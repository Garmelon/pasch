from __future__ import annotations

from abc import ABC, abstractmethod

from rich import print
from rich.markup import escape


class Module(ABC):
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.orchestrator.register(self)

    @abstractmethod
    def realize(self) -> None: ...


class Orchestrator:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

        self._frozen: bool = False
        self._modules: list[Module] = []

    def register(self, module: Module) -> None:
        if self._frozen:
            raise Exception("registering module wile orchestrator is frozen")
        self._modules.append(module)

    def realize(self) -> None:
        self._frozen = True
        for module in reversed(self._modules):
            print(f"[bold bright_magenta]\\[{escape(type(module).__name__)}]")
            module.realize()
