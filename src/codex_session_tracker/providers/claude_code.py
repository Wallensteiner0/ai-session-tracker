from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


def default_claude_projects_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECTS_DIR", Path.home() / ".claude" / "projects"))


def iter_jsonl_files(projects_dir: Path | None = None) -> Iterator[Path]:
    base = projects_dir or default_claude_projects_dir()
    if not base.exists():
        return
    for path in sorted(base.rglob("*.jsonl")):
        yield path


@dataclass
class ClaudeSession:
    session_id: str
    project_slug: str
    project_path: str | None
    ai_title: str | None
    model: str | None
    started_at: str | None
    ended_at: str | None
    duration_seconds: int | None
    version: str | None

    # token counts from message.usage (real values)
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_tokens: int | None = None
    cache_read_tokens: int | None = None
    tokens_are_real: bool = False  # True when sourced from message.usage

    # derived counts
    total_turns: int = 0
    user_turns: int = 0
    tool_call_count: int = 0
    tool_names: list[str] = field(default_factory=list)
    compact_events: int = 0
    compact_pre_tokens: int | None = None
    compact_post_tokens: int | None = None
    git_branch: str | None = None
    anomalies: list[str] = field(default_factory=list)

    def total_tokens_label(self) -> str:
        """Total token sum with reliability label."""
        if self.input_tokens is None and self.output_tokens is None:
            return "unbekannt"
        total = (self.input_tokens or 0) + (self.output_tokens or 0)
        label = "" if self.tokens_are_real else " (geschaetzt)"
        return f"{total}{label}"

    def to_dict(self) -> dict:
        d = {
            "session_id": self.session_id,
            "project_slug": self.project_slug,
            "project_path": self.project_path,
            "ai_title": self.ai_title,
            "model": self.model,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "version": self.version,
            "tokens": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "cache_creation": self.cache_creation_tokens,
                "cache_read": self.cache_read_tokens,
                "source": "message.usage" if self.tokens_are_real else "nicht verfuegbar",
            },
            "turns": {
                "user": self.user_turns,
                "assistant": self.total_turns,
            },
            "tool_calls": {
                "count": self.tool_call_count,
                "tools_used": sorted(set(self.tool_names)),
            },
            "compact": {
                "events": self.compact_events,
                "pre_tokens": self.compact_pre_tokens,
                "post_tokens": self.compact_post_tokens,
            },
            "git_branch": self.git_branch,
            "anomalies": self.anomalies,
            "tracker": {
                "source": "ai-session-tracker",
                "provider": "claude_code",
                "schema_version": 1,
            },
        }
        return d


def _parse_jsonl(path: Path) -> list[dict]:
    entries = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return entries


def _slug_to_path(slug: str) -> str | None:
    """Convert a project slug like -mnt-c-Users-...-MyProject to a readable path."""
    if slug.startswith("-"):
        candidate = slug[1:].replace("-", "/")
        parts = slug.lstrip("-").split("-")
        return "/" + "/".join(parts)
    return slug


def parse_session(jsonl_path: Path) -> ClaudeSession:
    """Parse one JSONL file into a ClaudeSession."""
    slug = jsonl_path.parent.name
    session_id = jsonl_path.stem
    entries = _parse_jsonl(jsonl_path)

    session = ClaudeSession(
        session_id=session_id,
        project_slug=slug,
        project_path=None,
        ai_title=None,
        model=None,
        started_at=None,
        ended_at=None,
        duration_seconds=None,
        version=None,
    )

    all_input = 0
    all_output = 0
    all_cache_create = 0
    all_cache_read = 0
    has_real_tokens = False
    timestamps = []

    for entry in entries:
        t = entry.get("type")

        # --- session metadata ---
        if t == "ai-title":
            session.ai_title = entry.get("aiTitle")

        elif t == "user":
            session.user_turns += 1
            ts = entry.get("timestamp")
            if ts:
                timestamps.append(ts)
            if not session.project_path:
                session.project_path = entry.get("cwd")
            if not session.version:
                session.version = entry.get("version")
            if not session.git_branch:
                session.git_branch = entry.get("gitBranch")

        elif t == "assistant":
            session.total_turns += 1
            msg = entry.get("message", {})

            # extract model
            if not session.model:
                session.model = msg.get("model")

            # extract usage
            usage = msg.get("usage", {})
            if usage:
                inp = usage.get("input_tokens", 0) or 0
                out = usage.get("output_tokens", 0) or 0
                cc = usage.get("cache_creation_input_tokens", 0) or 0
                cr = usage.get("cache_read_input_tokens", 0) or 0
                if inp or out:
                    all_input += inp
                    all_output += out
                    all_cache_create += cc
                    all_cache_read += cr
                    has_real_tokens = True

            # count tool_use blocks
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        session.tool_call_count += 1
                        name = block.get("name")
                        if name:
                            session.tool_names.append(name)

        elif t == "system":
            subtype = entry.get("subtype", "")
            ts = entry.get("timestamp")
            if ts:
                timestamps.append(ts)
            if not session.project_path:
                session.project_path = entry.get("cwd")
            if not session.version:
                session.version = entry.get("version")
            if not session.git_branch:
                session.git_branch = entry.get("gitBranch")

            if subtype == "compact_boundary":
                session.compact_events += 1
                meta = entry.get("compactMetadata", {})
                session.compact_pre_tokens = meta.get("preTokens")
                session.compact_post_tokens = meta.get("postTokens")

    # timestamps
    if timestamps:
        timestamps.sort()
        session.started_at = timestamps[0]
        session.ended_at = timestamps[-1]
        try:
            from datetime import datetime, timezone
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            def _parse(s):
                s = s.replace("+00:00", "Z")
                if "." not in s:
                    s = s.replace("Z", ".000Z")
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            start = _parse(session.started_at)
            end = _parse(session.ended_at)
            session.duration_seconds = int((end - start).total_seconds())
        except Exception:
            session.duration_seconds = None

    # token aggregation
    if has_real_tokens:
        session.input_tokens = all_input
        session.output_tokens = all_output
        session.cache_creation_tokens = all_cache_create
        session.cache_read_tokens = all_cache_read
        session.tokens_are_real = True

    # anomalies
    if session.duration_seconds and session.duration_seconds > 4 * 3600:
        session.anomalies.append("Sessiondauer > 4h")
    if session.compact_events > 0:
        session.anomalies.append(f"{session.compact_events} Compact-Event(s) erkannt")
    if session.output_tokens and session.output_tokens > 50000:
        session.anomalies.append("Hoher Output-Token-Verbrauch (> 50k)")
    if session.total_turns == 0:
        session.anomalies.append("Keine Antworten im Log")

    return session


def scan_sessions(projects_dir: Path | None = None) -> list[ClaudeSession]:
    """Scan all JSONL files and return parsed sessions, newest first."""
    sessions = []
    for path in iter_jsonl_files(projects_dir):
        sessions.append(parse_session(path))
    sessions.sort(key=lambda s: s.started_at or "", reverse=True)
    return sessions
