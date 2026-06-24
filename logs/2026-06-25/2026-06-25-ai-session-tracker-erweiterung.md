# Arbeitslog — ai-session-tracker Erweiterung

Datum: 2026-06-25

## Was wurde gemacht

- codex-session-tracker zu ai-session-tracker ausgebaut
- Claude-Code-JSONL-Parser implementiert (`providers/claude_code.py`)
- Token-Werte aus `message.usage` gelesen (echte Werte, kein Schätzen)
- CLI-Befehle `ai-tracker claude {scan,report,latest,export-obsidian,export-json}` ergänzt
- Obsidian-Pfade korrigiert: `03_Projects/ai-session-tracker/{codex,claude-code}/`
- WSL-Pfad-Übersetzung in `config.py` eingebaut
- Wrapper-Script `~/.local/bin/ai-tracker` für uv-managed Python angelegt
- Stop-Hook in `~/.claude/settings.json` gesetzt → Obsidian-Export nach jeder Session
- Git-Repo initialisiert, GitHub-Repo erstellt und gepusht (3 Commits)

## Offen

- Batch-Export: `export-obsidian` exportiert nur neueste Session
- Weitere Provider: OpenAI API, Ollama

## Nächster Schritt

`providers/openai_api.py` oder Batch-Export implementieren
