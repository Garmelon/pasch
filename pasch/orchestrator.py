from __future__ import annotations

import getpass
import socket
from typing import Callable, Concatenate

from rich.console import Console
from rich.markup import escape
from xdg_base_dirs import xdg_state_home


class Module:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.o = orchestrator
        self.o.register(self)
        self.c = self.o.c

    def configure(self) -> None:
        pass

    def execute(self) -> None:
        pass


def _snake_to_camel(s: str) -> str:
    return "".join(s.capitalize() for s in s.split("_"))


# Annotate a function with @module to turn it into a class implementing Module.
def module[**P](
    func: Callable[Concatenate[Orchestrator, P], None],
) -> Callable[Concatenate[Orchestrator, P], None]:
    def __init__(self, o: Orchestrator, *args: P.args, **kwargs: P.kwargs) -> None:
        super(self.__class__, self).__init__(o)
        self.args = args
        self.kwargs = kwargs

    def configure(self) -> None:
        # pyrefly: ignore
        return func(self.o, *self.args, **self.kwargs)

    # pyrefly: ignore
    return type(
        _snake_to_camel(func.__name__),
        (Module,),
        {"__init__": __init__, "configure": configure},
    )


# TODO @module_gen for generator-based modules


class Orchestrator:
    def __init__(self, name: str = "pasch", dry_run: bool = False) -> None:
        self.name = name
        self.dry_run = dry_run

        self.state_dir = xdg_state_home() / self.name
        self.c = Console(highlight=False)

        self.user = getpass.getuser()
        self.host = socket.gethostname()

        self._frozen: bool = False
        self._configured: bool = False
        self._modules: list[Module] = []

    def register(self, module: Module) -> None:
        if self._frozen:
            raise Exception("registering module wile orchestrator is frozen")
        self._modules.append(module)

    def configure(self) -> None:
        if self._configured:
            raise Exception("reconfiguring a configured orchestrator")

        self._frozen = True

        self.c.print()
        self.c.print("[bold bright_cyan]# Configure")
        for module in reversed(self._modules):
            self.c.print(f"[bold bright_magenta]\\[{escape(type(module).__name__)}]")
            module.configure()

        self._configured = True

    def execute(self) -> None:
        if not self._configured:
            raise Exception("executing an unconfigured orchestrator")

        self.c.print()
        self.c.print("[bold bright_cyan]# Execute")
        for module in self._modules:
            self.c.print(f"[bold bright_magenta]\\[{escape(type(module).__name__)}]")
            module.execute()

    def realize(self) -> None:
        self.configure()
        self.execute()
