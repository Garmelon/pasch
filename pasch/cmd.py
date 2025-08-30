import shlex
import subprocess

from rich import print
from rich.markup import escape


def run_execute(*cmd: str) -> None:
    print(f"[bright_black]$ {escape(shlex.join(cmd))}")
    subprocess.run(cmd, check=True)


def run_capture(*cmd: str) -> str:
    print(f"[bright_black italic]$ {escape(shlex.join(cmd))}")
    result = subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8")
    return result.stdout
