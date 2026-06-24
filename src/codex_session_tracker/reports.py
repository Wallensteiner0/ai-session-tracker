from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from .time_utils import human_duration


def _week_key(date_value: str) -> str:
    iso_year, iso_week, _ = datetime.fromisoformat(date_value).isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def build_report(sessions: list[dict]) -> str:
    if not sessions:
        return "Noch keine Sessions vorhanden."

    sessions_per_day = Counter(session["date"] for session in sessions)
    sessions_per_week = Counter(_week_key(session["date"]) for session in sessions)
    projects = Counter(session.get("project_name", "Unbekannt") for session in sessions)
    models = Counter(session.get("model", "Unbekannt") for session in sessions)
    total_seconds = sum(session.get("duration_seconds", 0) for session in sessions)
    average_seconds = total_seconds // len(sessions)

    lines = [
        "# Codex Tracker Report",
        "",
        f"Sessions gesamt: {len(sessions)}",
        f"Gesamtstunden: {total_seconds / 3600:.2f}",
        f"Durchschnittliche Sessiondauer: {human_duration(average_seconds)}",
        "",
        "## Sessions pro Tag",
        *[f"- {day}: {count}" for day, count in sorted(sessions_per_day.items())],
        "",
        "## Sessions pro Woche",
        *[f"- {week}: {count}" for week, count in sorted(sessions_per_week.items())],
        "",
        "## Projekte",
        *[f"- {project}: {count}" for project, count in projects.most_common()],
        "",
        "## Häufig verwendete Modelle",
        *[f"- {model}: {count}" for model, count in models.most_common()],
    ]
    return "\n".join(lines)
