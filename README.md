# pasch

Python-based Arch System Config Helper

```py
from argparse import ArgumentParser

from pasch import Orchestrator
from pasch.file import GitFile
from pasch.modules import Files, Pacman


def cfg_git(files: Files, pacman: Pacman) -> None:
    pacman.install("git")
    pacman.install("lazygit")

    git_config = GitFile()
    git_config.set("user", "name", "foo")
    git_config.set("user", "email", "foo@example.com")
    git_config.set("pull", "rebase", True)
    git_config.set("fetch", "prune", True)
    git_config.set("merge", "conflictstyle", "diff3")
    files.add(".config/git/config", git_config)


parser = ArgumentParser()
parser.add_argument("-d", "--dry-run", action="store_true")
args = parser.parse_args()

o = Orchestrator(dry_run=args.dry_run)

files = Files(o)
pacman = Pacman(o)
cfg_git(files, pacman)

o.realize()
```
