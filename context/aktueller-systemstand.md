# Aktueller Systemstand — ai-session-tracker

Stand: 2026-06-25

## Fortschritt 2026-06-24 / 2026-06-25

- Projekt von codex-session-tracker zu ai-session-tracker erweitert
- `providers/claude_code.py`: JSONL-Parser für `~/.claude/projects`, echte Token-Werte aus `message.usage`
- `claude_reports.py`: Markdown- und JSON-Report-Generierung
- CLI: `ai-tracker claude scan/report/latest/export-obsidian/export-json`
- `pyproject.toml`: Paketname `ai-session-tracker` v0.2.0, Einstiegspunkt `ai-tracker`
- Obsidian-Vault-Struktur: `03_Projects/ai-session-tracker/{codex,claude-code}/`
- WSL-Pfad-Übersetzung (`C:\...` → `/mnt/c/...`) eingebaut
- `~/.local/bin/ai-tracker` Wrapper-Script installiert (uv-managed Python, kein pip)
- Claude Code Stop-Hook in `~/.claude/settings.json` eingerichtet → automatischer Export nach Obsidian
- `.claude/settings.json` als Referenz ins Repo eingecheckt
- Repo initialisiert, auf GitHub gepusht: https://github.com/Wallensteiner0/ai-session-tracker

## Nächste Schritte

- `providers/openai_api.py` — OpenAI API Usage
- `providers/ollama.py` — lokale Ollama/Hermes Sessions
- `reports/cost_compare.py` — Kostenvergleich Cloud vs. lokal
- Batch-Export prüfen: `export-obsidian` exportiert derzeit nur die neueste Session
