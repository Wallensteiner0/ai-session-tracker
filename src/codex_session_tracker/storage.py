from __future__ import annotations

import json
from pathlib import Path

from . import config
from .markdown import obsidian_markdown, session_markdown


def ensure_dirs(root: Path) -> None:
    config.app_dir(root).mkdir(parents=True, exist_ok=True)
    config.checkpoints_dir(root).mkdir(parents=True, exist_ok=True)
    config.logs_dir(root).mkdir(parents=True, exist_ok=True)
    config.obsidian_dir(root).mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def active_session_exists(root: Path) -> bool:
    return config.current_session_path(root).exists()


def load_active_session(root: Path) -> dict:
    return read_json(config.current_session_path(root))


def save_active_session(root: Path, session: dict) -> None:
    ensure_dirs(root)
    write_json(config.current_session_path(root), session)


def clear_active_session(root: Path) -> None:
    path = config.current_session_path(root)
    if path.exists():
        path.unlink()


def next_session_id(root: Path, date: str) -> str:
    day_dir = config.logs_dir(root) / date
    existing = sorted(day_dir.glob("session-*.json")) if day_dir.exists() else []
    return f"session-{len(existing) + 1:03d}"


def persist_completed_session(root: Path, session: dict) -> tuple[Path, Path, Path]:
    day_dir = config.logs_dir(root) / session["date"]
    day_dir.mkdir(parents=True, exist_ok=True)

    base = session["session_id"]
    json_path = day_dir / f"{base}.json"
    md_path = day_dir / f"{base}.md"
    obsidian_path = config.obsidian_dir(root) / f"{session['date']}-{base}.md"

    write_json(json_path, session)
    md_path.write_text(session_markdown(session), encoding="utf-8")
    obsidian_path.write_text(obsidian_markdown(session), encoding="utf-8")
    return json_path, md_path, obsidian_path


def iter_sessions(root: Path) -> list[dict]:
    sessions: list[dict] = []
    for path in sorted(config.logs_dir(root).glob("*/*.json")):
        try:
            sessions.append(read_json(path))
        except json.JSONDecodeError:
            continue
    return sessions
