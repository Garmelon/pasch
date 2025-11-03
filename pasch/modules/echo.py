from pasch.orchestrator import Module, Orchestrator
from pasch.util import run_execute


class Echo(Module):
    def __init__(self, orchestrator: Orchestrator) -> None:
        super().__init__(orchestrator)
        self.args: list[str] = []

    def add(self, arg: str) -> None:
        self.args.append(arg)

    def realize(self) -> None:
        run_execute("echo", *self.args)
