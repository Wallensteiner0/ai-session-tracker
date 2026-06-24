from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import checkpoints, config, git_utils, storage
from .prompts import ask, ask_rating, ask_yes_no
from .reports import build_report
from .time_utils import duration_seconds, human_duration, now_iso


def _finish_session_with_snapshot(session: dict, ended_at: str, mode: str, reason: str) -> None:
    root = config.project_root()
    git = git_utils.snapshot(root)

    session["ended_at"] = ended_at
    session["duration_seconds"] = duration_seconds(session["started_at"], ended_at)
    session["git"]["branch_end"] = git.branch
    session["git"]["commit_end"] = git.commit
    session["git"]["status_end"] = git_utils.status(root)
    session["changed_files"] = git_utils.changed_files(root)
    session["new_commits"] = git_utils.commits_between(
        root,
        session["git"].get("commit_start"),
        git.commit,
    )
    session["end_detection"] = {
        "mode": mode,
        "reason": reason,
        "detected_at": now_iso(),
    }


def recover_stale_session_if_needed() -> bool:
    root = config.project_root()
    if not storage.active_session_exists(root):
        return False

    session = storage.load_active_session(root)
    gap_seconds = checkpoints.seconds_since_last_checkpoint(session)
    if gap_seconds < config.STALE_SESSION_SECONDS:
        return False

    last_checkpoint = checkpoints.last_checkpoint(session)
    ended_at = (last_checkpoint or {}).get("at") or session["started_at"]
    _finish_session_with_snapshot(
        session,
        ended_at,
        "auto_stale_checkpoint",
        f"Letzter Checkpoint liegt mindestens {human_duration(config.STALE_SESSION_SECONDS)} zurueck.",
    )
    session["result"] = {
        "limit_reached": True,
        "codex_usage": "Nicht erfasst; Session wurde automatisch wegen Zeitluecke abgeschlossen.",
        "rating": None,
        "learnings": "Automatischer Abschluss nach inaktiver oder unterbrochener Session.",
    }

    json_path, md_path, obsidian_path = storage.persist_completed_session(root, session)
    storage.clear_active_session(root)
    print("Verwaiste Session automatisch abgeschlossen.")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Obsidian: {obsidian_path}")
    return True


def start_session() -> int:
    root = config.project_root()
    storage.ensure_dirs(root)
    recover_stale_session_if_needed()

    if storage.active_session_exists(root):
        print("Es laeuft bereits eine Session. Nutze `codex-tracker status`, `codex-tracker checkpoint` oder `codex-tracker end`.")
        return 1

    started_at = now_iso()
    date = datetime.fromisoformat(started_at).date().isoformat()
    git = git_utils.snapshot(root)

    session = {
        "session_id": storage.next_session_id(root, date),
        "date": date,
        "project_name": ask("Projektname", root.name),
        "goal": ask("Ziel der Session"),
        "model": ask("Verwendetes Modell", "GPT-5 Codex"),
        "notes": ask("Optionale Notizen", ""),
        "started_at": started_at,
        "ended_at": None,
        "duration_seconds": None,
        "working_directory": str(root),
        "git": {
            "is_repo": git.is_repo,
            "branch_start": git.branch,
            "commit_start": git.commit,
            "branch_end": None,
            "commit_end": None,
            "status_end": None,
        },
        "changed_files": [],
        "new_commits": [],
        "checkpoints": [],
        "last_checkpoint_at": None,
        "end_detection": {
            "mode": None,
            "reason": None,
            "detected_at": None,
        },
        "result": {},
        "tracker": {
            "source": "codex-session-tracker",
            "schema_version": 1,
        },
    }

    storage.save_active_session(root, session)
    checkpoints.write_checkpoint(root, session, "session_start")
    print(f"Session gestartet: {session['session_id']} ({session['project_name']})")
    return 0


def end_session() -> int:
    root = config.project_root()
    if not storage.active_session_exists(root):
        print("Keine aktive Session gefunden.")
        return 1

    session = storage.load_active_session(root)
    ended_at = now_iso()
    checkpoints.write_checkpoint(root, session, "manual_end")

    _finish_session_with_snapshot(session, ended_at, "manual", "Session wurde mit codex-tracker end beendet.")
    session["result"] = {
        "limit_reached": ask_yes_no("Limit erreicht?"),
        "codex_usage": ask("Codex Usage laut /usage", ""),
        "rating": ask_rating("Persoenliche Bewertung (1-5)"),
        "learnings": ask("Wichtigste Erkenntnisse", ""),
    }

    json_path, md_path, obsidian_path = storage.persist_completed_session(root, session)
    storage.clear_active_session(root)

    print(f"Session beendet: {session['session_id']} ({human_duration(session['duration_seconds'])})")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Obsidian: {obsidian_path}")
    return 0


def show_status() -> int:
    root = config.project_root()
    if recover_stale_session_if_needed():
        return 0

    if not storage.active_session_exists(root):
        print("Keine aktive Session.")
        return 0

    session = storage.load_active_session(root)
    checkpoints.write_checkpoint(root, session, "status")
    elapsed = duration_seconds(session["started_at"], now_iso())
    gap = checkpoints.seconds_since_last_checkpoint(session)
    print(f"Aktive Session: {session['session_id']}")
    print(f"Projekt: {session['project_name']}")
    print(f"Ziel: {session['goal']}")
    print(f"Modell: {session['model']}")
    print(f"Laeuft seit: {human_duration(elapsed)}")
    print(f"Branch: {session['git'].get('branch_start') or '-'}")
    print(f"Letzter Checkpoint: vor {human_duration(gap)}")
    return 0


def create_checkpoint() -> int:
    root = config.project_root()
    if recover_stale_session_if_needed():
        return 0

    if not storage.active_session_exists(root):
        print("Keine aktive Session.")
        return 1

    session = storage.load_active_session(root)
    checkpoint = checkpoints.write_checkpoint(root, session, "manual_checkpoint")
    print(f"Checkpoint gespeichert: {checkpoint['at']}")
    print(f"Geaenderte Dateien: {len(checkpoint['changed_files'])}")
    return 0


def show_report() -> int:
    root = config.project_root()
    recover_stale_session_if_needed()
    print(build_report(storage.iter_sessions(root)))
    return 0


# ── claude subcommands ────────────────────────────────────────────────────────

def _claude_projects_dir() -> Path | None:
    from .providers.claude_code import default_claude_projects_dir
    d = default_claude_projects_dir()
    return d if d.exists() else None


def claude_scan() -> int:
    from .providers.claude_code import scan_sessions
    d = _claude_projects_dir()
    if d is None:
        print("Kein Claude-Projekte-Verzeichnis gefunden (~/.claude/projects).")
        return 1
    sessions = scan_sessions(d)
    print(f"{len(sessions)} Claude-Code-Session(s) gefunden unter {d}")
    for s in sessions[:10]:
        from .claude_reports import _fmt_date
        date = _fmt_date(s.started_at)[:10] if s.started_at else "-"
        project = Path(s.project_path).name if s.project_path else s.project_slug
        inp = f"{s.input_tokens:,}" if s.input_tokens is not None else "n/a"
        out = f"{s.output_tokens:,}" if s.output_tokens is not None else "n/a"
        print(f"  {date}  {project:<30}  in:{inp}  out:{out}  tools:{s.tool_call_count}")
    if len(sessions) > 10:
        print(f"  ... und {len(sessions) - 10} weitere")
    return 0


def claude_report() -> int:
    from .providers.claude_code import scan_sessions
    from .claude_reports import sessions_to_report_markdown
    d = _claude_projects_dir()
    sessions = scan_sessions(d) if d else []
    print(sessions_to_report_markdown(sessions))
    return 0


def claude_latest() -> int:
    from .providers.claude_code import scan_sessions
    from .claude_reports import session_to_markdown
    d = _claude_projects_dir()
    sessions = scan_sessions(d) if d else []
    if not sessions:
        print("Keine Sessions gefunden.")
        return 1
    print(session_to_markdown(sessions[0]))
    return 0


def claude_export_obsidian() -> int:
    from .providers.claude_code import scan_sessions
    from .claude_reports import session_to_markdown
    d = _claude_projects_dir()
    sessions = scan_sessions(d) if d else []
    if not sessions:
        print("Keine Sessions gefunden.")
        return 1

    session = sessions[0]
    obsidian_base = config.obsidian_claude_dir()
    obsidian_base.mkdir(parents=True, exist_ok=True)
    date = (session.started_at or "")[:10] or "unknown"
    filename = f"{date}-{session.session_id[:8]}.md"
    out_path = obsidian_base / filename
    out_path.write_text(session_to_markdown(session), encoding="utf-8")
    print(f"Obsidian-Export: {out_path}")
    return 0


def claude_export_json() -> int:
    from .providers.claude_code import scan_sessions
    from .claude_reports import session_to_json
    d = _claude_projects_dir()
    sessions = scan_sessions(d) if d else []
    if not sessions:
        print("Keine Sessions gefunden.")
        return 1
    print(session_to_json(sessions[0]))
    return 0


# ── parser ────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-tracker",
        description="AI Session Tracker — Codex, Claude-Code und mehr",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # legacy codex commands (kept as-is)
    subparsers.add_parser("start", help="Neue Codex-Session starten")
    subparsers.add_parser("end", help="Aktive Codex-Session beenden")
    subparsers.add_parser("status", help="Aktive Session anzeigen")
    subparsers.add_parser("checkpoint", help="Zwischenstand der aktiven Session speichern")
    subparsers.add_parser("report", help="Auswertung aller Codex-Sessions anzeigen")

    # claude subcommands
    claude_p = subparsers.add_parser("claude", help="Claude-Code-Sessions auswerten")
    claude_sub = claude_p.add_subparsers(dest="claude_cmd", required=True)
    claude_sub.add_parser("scan", help="Alle Claude-Sessions auflisten")
    claude_sub.add_parser("report", help="Zusammenfassenden Report anzeigen")
    claude_sub.add_parser("latest", help="Neueste Session als Markdown anzeigen")
    claude_sub.add_parser("export-obsidian", help="Neueste Session nach Obsidian exportieren")
    claude_sub.add_parser("export-json", help="Neueste Session als JSON ausgeben")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "claude":
        claude_commands = {
            "scan": claude_scan,
            "report": claude_report,
            "latest": claude_latest,
            "export-obsidian": claude_export_obsidian,
            "export-json": claude_export_json,
        }
        raise SystemExit(claude_commands[args.claude_cmd]())

    commands = {
        "start": start_session,
        "end": end_session,
        "status": show_status,
        "checkpoint": create_checkpoint,
        "report": show_report,
    }
    raise SystemExit(commands[args.command]())
