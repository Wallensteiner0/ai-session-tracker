---
Status: Entwurf
Erstellt: 2026-06-25
Ziel: 05_Decisions oder 07_AI_Context/Agentic_OS
---

# Entscheidungen — ai-session-tracker

## Architektur

**Token-Verlässlichkeit:** Werte aus `message.usage` werden als echt markiert (`tokens_are_real=True`). Alles ohne diese Quelle wird explizit als Schätzung gekennzeichnet — keine falsche Genauigkeit.

**WSL-Pfad-Übersetzung:** `config._wsl_translate()` wandelt Windows-Pfade (`C:\...`) automatisch in WSL-Pfade (`/mnt/c/...`) um. Keine manuelle Konfiguration nötig.

**Installation ohne pip:** System nutzt uv-managed Python. Lösung: Wrapper-Script `~/.local/bin/ai-tracker` mit hardkodiertem `sys.path`. Kein venv, kein Systemeingriff.

**Obsidian-Vault-Struktur:**
```
03_Projects/ai-session-tracker/
  codex/        ← manuelle Codex-Sessions
  claude-code/  ← automatisch via Stop-Hook
```

**Stop-Hook:** `~/.claude/settings.json` feuert `ai-tracker claude export-obsidian` nach jeder Claude-Code-Session. Konfiguration liegt auch unter `.claude/settings.json` im Repo.

## Offene Fragen

- Batch-Export: alle Sessions eines Tages, nicht nur die neueste
- Provider-Erweiterungen: OpenAI API, Ollama
