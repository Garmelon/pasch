from __future__ import annotations

import getpass
import socket
from abc import ABC, abstractmethod
from typing import Callable, Concatenate

from rich import print
from rich.console import Console
from rich.markup import escape
from xdg_base_dirs import xdg_state_home


class Module(ABC):
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.orchestrator.register(self)
        self.c = self.orchestrator.console

    @abstractmethod
    def realize(self) -> None: ...


def _snake_to_camel(s: str) -> str:
    return "".join(s.capitalize() for s in s.split("_"))


# Annotate a function with @module to turn it into a class implementing Module.
def module[**P](
    func: Callable[Concatenate[Orchestrator, P], None],
) -> Callable[Concatenate[Orchestrator, P], None]:
    def __init__(
        self,
        orchestrator: Orchestrator,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        super(self.__class__, self).__init__(orchestrator)
        self.args = args
        self.kwargs = kwargs

    def realize(self) -> None:
        # pyrefly: ignore
        return func(self.orchestrator, *self.args, **self.kwargs)

    # pyrefly: ignore
    return type(
        _snake_to_camel(func.__name__),
        (Module,),
        {"__init__": __init__, "realize": realize},
    )


class Orchestrator:
    def __init__(self, name: str = "pasch", dry_run: bool = False) -> None:
        self.name = name
        self.dry_run = dry_run

        self.state_dir = xdg_state_home() / self.name
        self.console = Console(highlight=False)

        self.user = getpass.getuser()
        self.host = socket.gethostname()

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
