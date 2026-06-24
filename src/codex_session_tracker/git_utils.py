from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitSnapshot:
    branch: str | None
    commit: str | None
    is_repo: bool


def run_git(args: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def snapshot(cwd: Path) -> GitSnapshot:
    is_repo = run_git(["rev-parse", "--is-inside-work-tree"], cwd) == "true"
    if not is_repo:
        return GitSnapshot(branch=None, commit=None, is_repo=False)

    branch = run_git(["branch", "--show-current"], cwd) or "DETACHED"
    commit = run_git(["rev-parse", "HEAD"], cwd)
    return GitSnapshot(branch=branch, commit=commit, is_repo=True)


def status(cwd: Path) -> str:
    return run_git(["status", "--short"], cwd) or ""


def changed_files(cwd: Path) -> list[str]:
    output = status(cwd)
    files: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return files


def commits_between(cwd: Path, start_commit: str | None, end_commit: str | None) -> list[str]:
    if not start_commit or not end_commit or start_commit == end_commit:
        return []
    output = run_git(["log", "--oneline", f"{start_commit}..{end_commit}"], cwd)
    if not output:
        return []
    return output.splitlines()
