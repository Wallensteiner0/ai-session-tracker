from __future__ import annotations

from .time_utils import human_duration


def _list_or_dash(items: list[str]) -> str:
    if not items:
        return "- Keine"
    return "\n".join(f"- {item}" for item in items)


def session_markdown(session: dict) -> str:
    duration = human_duration(session.get("duration_seconds", 0))
    commits = session.get("new_commits", [])
    changed_files = session.get("changed_files", [])
    result = session.get("result", {})
    end_detection = session.get("end_detection", {})

    return f"""# Codex Session

Datum: {session.get("date", "")}
Projekt: {session.get("project_name", "")}
Ziel: {session.get("goal", "")}
Dauer: {duration}
Branch: {session.get("git", {}).get("branch_start") or "-"}
Commits:
{_list_or_dash(commits)}
Ergebnis: Bewertung {result.get("rating", "-")}/5
Learnings: {result.get("learnings", "-")}

## Details

- Session-ID: {session.get("session_id", "")}
- Modell: {session.get("model", "")}
- Arbeitsverzeichnis: {session.get("working_directory", "")}
- Start: {session.get("started_at", "")}
- Ende: {session.get("ended_at", "")}
- Abschlussart: {end_detection.get("mode", "manual")}
- Limit erreicht: {"ja" if result.get("limit_reached") else "nein"}
- Codex Usage: {result.get("codex_usage", "-")}
- Checkpoints: {len(session.get("checkpoints", []))}

## Geänderte Dateien

{_list_or_dash(changed_files)}

## Git Status

```text
{session.get("git", {}).get("status_end") or "clean"}
```

## Notizen

{session.get("notes") or "-"}
"""


def obsidian_markdown(session: dict) -> str:
    duration = human_duration(session.get("duration_seconds", 0))
    commits = session.get("new_commits", [])
    result = session.get("result", {})
    end_detection = session.get("end_detection", {})

    return f"""# Codex Session

Datum: {session.get("date", "")}
Projekt: {session.get("project_name", "")}
Ziel: {session.get("goal", "")}
Dauer: {duration}
Branch: {session.get("git", {}).get("branch_start") or "-"}
Commits:
{_list_or_dash(commits)}
Ergebnis: Bewertung {result.get("rating", "-")}/5
Abschlussart: {end_detection.get("mode", "manual")}
Learnings: {result.get("learnings", "-")}
"""
