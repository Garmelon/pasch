import difflib
import shlex
import subprocess

from rich import print
from rich.markup import escape
from rich.syntax import Syntax


def run_execute(*cmd: str) -> None:
    print(f"[bright_black]$ {escape(shlex.join(cmd))}")
    subprocess.run(cmd, check=True)


def run_capture(*cmd: str) -> str:
    print(f"[bright_black]$ {escape(shlex.join(cmd))}")
    result = subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8")
    return result.stdout


def fmt_diff(old: str, new: str, old_name="old", new_name="new") -> Syntax:
    diff_text = "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=old_name,
            tofile=new_name,
            lineterm="\n",
        )
    )
    return Syntax(diff_text, "diff", line_numbers=False)


def prompt(question: str, default: bool | None = None) -> bool:
    default_str = {True: "[Y/n]", False: "[y/N]", None: "[y/n]"}[default]
    while True:
        reply = input(f"{question} {default_str} ").strip().lower()
        if not reply and default is not None:
            return default
        if reply in {"y", "yes"}:
            return True
        if reply in {"n", "no"}:
            return False
        print("Please enter y/yes or n/no.")
