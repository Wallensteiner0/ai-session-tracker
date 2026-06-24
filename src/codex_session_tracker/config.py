from __future__ import annotations

import os
from pathlib import Path


APP_DIR = ".codex-tracker"
CURRENT_SESSION_FILE = "current-session.json"
LOGS_DIR = "logs"
CHECKPOINTS_DIR = "checkpoints"
STALE_SESSION_SECONDS = 2 * 60 * 60

# Vault root: 03_Projects\ai-session-tracker\
# Codex project sessions go into:  03_Projects\ai-session-tracker\<project-name>\
# Claude Code sessions go into:    03_Projects\ai-session-tracker\claude-code\
DEFAULT_OBSIDIAN_AI_TRACKER_DIR = Path(
    r"C:\Users\walle\Nextcloud2\OBSIDIAN\AI-Knowledge-System\03_Projects\ai-session-tracker"
)
OBSIDIAN_AI_TRACKER_ENV = "AI_TRACKER_OBSIDIAN_DIR"

# Legacy alias kept for callers that still reference the old constant
DEFAULT_OBSIDIAN_PROJECTS_DIR = DEFAULT_OBSIDIAN_AI_TRACKER_DIR
OBSIDIAN_PROJECTS_ENV = OBSIDIAN_AI_TRACKER_ENV


def project_root() -> Path:
    return Path.cwd()


def app_dir(root: Path) -> Path:
    return root / APP_DIR


def current_session_path(root: Path) -> Path:
    return app_dir(root) / CURRENT_SESSION_FILE


def checkpoints_dir(root: Path) -> Path:
    return app_dir(root) / CHECKPOINTS_DIR


def logs_dir(root: Path) -> Path:
    return root / LOGS_DIR


def _wsl_translate(p: Path) -> Path:
    """Translate a Windows path (C:\\...) to /mnt/c/... when running under WSL."""
    s = str(p)
    if os.name != "nt" and len(s) >= 3 and s[1] == ":" and s[2] in ("/", "\\"):
        drive = s[0].lower()
        rest = s[3:].replace("\\", "/")
        return Path(f"/mnt/{drive}/{rest}")
    return p


def obsidian_ai_tracker_dir() -> Path:
    """Root of the ai-session-tracker vault folder, WSL-translated if needed."""
    raw = Path(os.environ.get(OBSIDIAN_AI_TRACKER_ENV, DEFAULT_OBSIDIAN_AI_TRACKER_DIR))
    return _wsl_translate(raw)


def obsidian_dir(root: Path) -> Path:
    """Codex project sessions: 03_Projects/ai-session-tracker/codex/"""
    return obsidian_ai_tracker_dir() / "codex"


def obsidian_claude_dir() -> Path:
    """Claude Code sessions: 03_Projects/ai-session-tracker/claude-code/"""
    return obsidian_ai_tracker_dir() / "claude-code"
