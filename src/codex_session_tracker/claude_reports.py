from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .providers.claude_code import ClaudeSession


def _human_duration(seconds):
    if seconds is None:
        return "-"
    h, rem = divmod(abs(seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _fmt_date(iso):
    if not iso:
        return "-"
    try:
        iso = iso.replace("+00:00", "Z")
        if "." not in iso:
            iso = iso.replace("Z", ".000Z")
        dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso


def session_to_markdown(session: ClaudeSession) -> str:
    real = session.tokens_are_real
    token_note = "" if real else " *(aus Logdaten abgeleitet)*"

    inp = f"{session.input_tokens:,}" if session.input_tokens is not None else "nicht erfasst"
    out = f"{session.output_tokens:,}" if session.output_tokens is not None else "nicht erfasst"
    cr = f"{session.cache_read_tokens:,}" if session.cache_read_tokens is not None else "nicht erfasst"
    cw = f"{session.cache_creation_tokens:,}" if session.cache_creation_tokens is not None else "nicht erfasst"

    nl = "\n"
    anomalies_block = "keine" if not session.anomalies else nl.join(
        f"- {a}" for a in session.anomalies
    )

    tool_counts: dict[str, int] = {}
    for name in session.tool_names:
        tool_counts[name] = tool_counts.get(name, 0) + 1
    tools_block = "keine" if not tool_counts else nl.join(
        f"- {t}: {c}x" for t, c in sorted(tool_counts.items())
    )

    recommendations = []
    if session.compact_events:
        recommendations.append(
            f"Autocompact wurde {session.compact_events}x ausgeloest "
            f"(vor Compact: {session.compact_pre_tokens or '?'} Tokens, "
            f"danach: {session.compact_post_tokens or '?'} Tokens). "
            "Erwaege kluerzere Sessions oder regelmaessige /clear-Aufrufe."
        )
    if session.output_tokens and session.output_tokens > 50000:
        recommendations.append("Hoher Output-Verbrauch. Grosse Dateiinhalte in Antworten vermeiden.")
    if not recommendations:
        recommendations.append("Keine besonderen Auffaelligkeiten.")

    rec_block = nl.join(f"- {r}" for r in recommendations)
    date_str = _fmt_date(session.started_at)[:10] if session.started_at else "-"

    lines = [
        "# Claude Code Session Report",
        "",
        f"Datum: {date_str}",
        f"Projekt: {session.project_path or session.project_slug}",
        f"Modell: {session.model or 'unbekannt'}",
        f"Start: {_fmt_date(session.started_at)}",
        f"Ende: {_fmt_date(session.ended_at)}",
        f"Dauer: {_human_duration(session.duration_seconds)}",
        f"Geschaetzte Token gesamt: {session.total_tokens_label()}",
        f"Input Tokens: {inp}{token_note}",
        f"Output Tokens: {out}{token_note}",
        f"Cache Read: {cr}",
        f"Cache Write: {cw}",
        f"Tool Calls: {session.tool_call_count}",
        f"Compact Events: {session.compact_events}",
        "",
        "## Tool-Nutzung",
        "",
        tools_block,
        "",
        "## Auffaelligkeiten",
        "",
        anomalies_block,
        "",
        "## Empfehlungen",
        "",
        rec_block,
        "",
        "---",
        f"Session-ID: `{session.session_id}`",
        f"Git-Branch: {session.git_branch or '-'}",
        f"Claude Code Version: {session.version or '-'}",
    ]
    return "\n".join(lines)


def sessions_to_report_markdown(sessions, title: str = "Claude Code Sessions") -> str:
    if not sessions:
        return "# Keine Claude-Code-Sessions gefunden."

    total_input = sum(s.input_tokens or 0 for s in sessions if s.tokens_are_real)
    total_output = sum(s.output_tokens or 0 for s in sessions if s.tokens_are_real)
    total_tools = sum(s.tool_call_count for s in sessions)
    total_compacts = sum(s.compact_events for s in sessions)
    total_turns = sum(s.total_turns for s in sessions)

    lines = [
        f"# {title}",
        "",
        f"Sessions: {len(sessions)}",
        f"Total Input Tokens: {total_input:,} (nur Sessions mit echten Werten)",
        f"Total Output Tokens: {total_output:,} (nur Sessions mit echten Werten)",
        f"Total Tool Calls: {total_tools}",
        f"Total Assistant-Turns: {total_turns}",
        f"Total Compact-Events: {total_compacts}",
        "",
        "## Sessions",
        "",
    ]

    for s in sessions:
        date = _fmt_date(s.started_at)[:10] if s.started_at else "-"
        project = Path(s.project_path).name if s.project_path else s.project_slug
        dur = _human_duration(s.duration_seconds)
        inp = f"{s.input_tokens:,}" if s.input_tokens is not None else "n/a"
        out = f"{s.output_tokens:,}" if s.output_tokens is not None else "n/a"
        lines.append(
            f"- **{date}** | {project} | {s.model or '?'} | {dur} | "
            f"in:{inp} out:{out} | tools:{s.tool_call_count}"
        )

    return "\n".join(lines)


def session_to_json(session: ClaudeSession) -> str:
    return json.dumps(session.to_dict(), indent=2, ensure_ascii=False)
