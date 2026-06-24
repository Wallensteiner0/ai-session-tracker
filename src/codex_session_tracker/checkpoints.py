from __future__ import annotations

from pathlib import Path

from . import config, git_utils, storage
from .time_utils import duration_seconds, now_iso


def _safe_timestamp(value: str) -> str:
    return value.replace(":", "-").replace("+", "_").replace(".", "-")


def build_checkpoint(root: Path, session: dict, reason: str) -> dict:
    git = git_utils.snapshot(root)
    return {
        "at": now_iso(),
        "reason": reason,
        "git": {
            "branch": git.branch,
            "commit": git.commit,
            "status": git_utils.status(root),
        },
        "changed_files": git_utils.changed_files(root),
    }


def write_checkpoint(root: Path, session: dict, reason: str) -> dict:
    checkpoint = build_checkpoint(root, session, reason)
    session.setdefault("checkpoints", []).append(checkpoint)
    session["last_checkpoint_at"] = checkpoint["at"]
    storage.save_active_session(root, session)

    checkpoint_dir = config.checkpoints_dir(root) / session["session_id"]
    checkpoint_path = checkpoint_dir / f"{_safe_timestamp(checkpoint['at'])}.json"
    storage.write_json(checkpoint_path, checkpoint)
    return checkpoint


def seconds_since_last_checkpoint(session: dict, now_value: str | None = None) -> int:
    reference = session.get("last_checkpoint_at") or session["started_at"]
    return duration_seconds(reference, now_value or now_iso())


def last_checkpoint(session: dict) -> dict | None:
    checkpoints = session.get("checkpoints") or []
    if not checkpoints:
        return None
    return checkpoints[-1]
