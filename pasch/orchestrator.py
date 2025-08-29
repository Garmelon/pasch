from __future__ import annotations

from abc import ABC, abstractmethod


class Module(ABC):
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.orchestrator.register(self)

    @abstractmethod
    def realize(self) -> None: ...


class Orchestrator:
    def __init__(self) -> None:
        self.frozen: bool = False
        self.modules: list[Module] = []

    def register(self, module: Module) -> None:
        if self.frozen:
            raise Exception("registering module wile orchestrator is frozen")
        self.modules.append(module)

    def realize(self) -> None:
        self.frozen = True
        for module in reversed(self.modules):
            module.realize()
