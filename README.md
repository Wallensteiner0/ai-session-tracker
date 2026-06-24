# ai-session-tracker

Lokales Python-Projekt fuer das Dokumentieren und Auswerten von AI-Sessions (Codex, Claude Code und mehr).

Das Tool speichert Codex-Sessions als JSON und Markdown, analysiert automatisch Claude-Code-JSONL-Logs, und erzeugt Obsidian-kompatible Reports.

---

## CLI-Einstiegspunkte

| Befehl       | Zweck                              |
|--------------|------------------------------------|
| `ai-tracker` | Neuer Hauptbefehl                  |
| `codex-tracker` | Legacy-Alias, weiterhin gueltig |

---

## Codex-Sessions (manueller Workflow)

### Session starten

```powershell
ai-tracker start
```

Fragt ab: Projektname, Ziel, Modell, Notizen.
Speichert automatisch: Startzeit, Git-Branch, Commit, Arbeitsverzeichnis.

### Status / Checkpoint / Ende

```powershell
ai-tracker status
ai-tracker checkpoint
ai-tracker end
```

`end` fragt manuell: Limit erreicht, Codex Usage, Bewertung, Erkenntnisse.
Checkpoints schuetzen vor Token-Ende-Abbruch. Sessions mit > 2h Inaktivitaet werden automatisch abgeschlossen.

### Session-Report

```powershell
ai-tracker report
```

Zeigt: Sessions pro Tag/Woche, Gesamtstunden, Projekte, Modelle, durchschnittliche Dauer.

---

## Claude-Code-Sessions (automatisch aus Logs)

Claude Code schreibt alle Sessions als JSONL-Dateien nach `~/.claude/projects/`.
Der Tracker liest diese Logs direkt aus und extrahiert:

- Modellname
- Start- und Endzeit (aus Timestamps)
- Echte Token-Werte aus `message.usage` (input, output, cache_read, cache_creation)
- Anzahl User- und Assistant-Turns
- Tool-Calls mit Namen und Haeufigkeit
- Compact-Events (Autocompact-Trigger mit pre/post Token-Werten)
- Git-Branch und Claude-Code-Version
- Anomalien (hoher Verbrauch, lange Sessiondauer, fehlende Antworten)

**Hinweis zur Token-Zuverlaessigkeit:**
Die Token-Werte werden direkt aus `message.usage` in den Logs gelesen und sind damit echt und verifiziert — allerdings zaehlt jede Antwort separat, nicht kumuliert ueber die gesamte Session. Werte ohne `message.usage`-Quelle werden explizit als Schaetzung markiert.

### Befehle

```bash
# Alle Sessions auflisten
ai-tracker claude scan

# Zusammenfassenden Report aller Sessions anzeigen
ai-tracker claude report

# Neueste Session als Markdown-Report anzeigen
ai-tracker claude latest

# Neueste Session nach Obsidian exportieren
ai-tracker claude export-obsidian

# Neueste Session als JSON ausgeben
ai-tracker claude export-json
```

### Automatischer Report nach jeder Session

Empfehlung: Claude-Code-Hook am Session-Ende.

**Option 1: Claude Code after-turn Hook**

Fuge in `~/.claude/settings.json` ein:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -m codex_session_tracker claude latest >> ~/claude-session-log.md"
          }
        ]
      }
    ]
  }
}
```

**Option 2: Shell-Alias**

```bash
alias cc-done="ai-tracker claude latest"
alias cc-obsidian="ai-tracker claude export-obsidian"
```

Rufe manuell nach jeder Session auf:

```bash
cc-obsidian
```

**Option 3: Cronjob (taegliche Zusammenfassung)**

```bash
# crontab -e
0 23 * * * python3 -m codex_session_tracker claude report > ~/claude-daily.md
```

---

## Installation

```powershell
cd C:\Users\walle\Documents\Projekte\codex-session-tracker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

```bash
# WSL / Linux
cd /mnt/c/Users/walle/Documents/Projekte/codex-session-tracker
pip install -e .
ai-tracker --help
```

---

## Report-Format (Claude Code)

```markdown
# Claude Code Session Report

Datum: 2026-06-24
Projekt: /mnt/c/Users/walle/Documents/Projekte
Modell: anthropic/claude-4.6-sonnet-20260217
Start: 2026-06-24 20:30 UTC
Ende: 2026-06-24 21:14 UTC
Dauer: 43m 37s
Geschaetzte Token gesamt: 75752
Input Tokens: 108
Output Tokens: 75,644
Cache Read: 2,982,602
Cache Write: 425,413
Tool Calls: 41
Compact Events: 0

## Tool-Nutzung

- Bash: 18x
- Edit: 3x
- Read: 8x
- Write: 3x

## Auffaelligkeiten

- Hoher Output-Token-Verbrauch (> 50k)

## Empfehlungen

- Hoher Output-Verbrauch. Grosse Dateiinhalte in Antworten vermeiden.
```

Beispiele: `logs/example-claude-report.md` und `logs/example-claude-report.json`

---

## Ordnerstruktur

```text
codex-session-tracker/        (Paketname: ai-session-tracker)
  pyproject.toml
  README.md
  src/
    codex_session_tracker/
      cli.py                  # Erweitert: ai-tracker claude ...
      config.py
      markdown.py
      reports.py
      storage.py
      claude_reports.py       # NEU: Markdown/JSON-Report fuer Claude-Sessions
      providers/
        __init__.py
        claude_code.py        # NEU: JSONL-Parser fuer ~/.claude/projects/
  logs/
    YYYY-MM-DD/
      session-001.json
      session-001.md
    example-claude-report.md
    example-claude-report.json
```

---

## Erweiterungsstruktur (geplant)

Das Projekt ist strukturell vorbereitet fuer:

| Provider               | Status   | Geplantes Modul                   |
|------------------------|----------|-----------------------------------|
| OpenAI Codex (manuell) | aktiv    | `cli.py` (manueller Workflow)     |
| Claude Code (JSONL)    | aktiv    | `providers/claude_code.py`        |
| OpenAI API Usage       | geplant  | `providers/openai_api.py`         |
| Ollama / Hermes lokal  | geplant  | `providers/ollama.py`             |
| Headroom-Vergleich     | geplant  | `reports/headroom.py`             |
| Kostenvergleich        | geplant  | `reports/cost_compare.py`         |
| Obsidian Daily Notes   | geplant  | `export/obsidian_daily.py`        |

---

## Architekturentscheidungen

- `argparse` statt CLI-Framework: keine Runtime-Abhaengigkeiten.
- Shell-Git statt GitPython: kein mandatory Dependency.
- JSON als kanonisches Format: spaeter gut in SQLite oder Dashboard migrierbar.
- Provider-Modul-Struktur: jeder AI-Anbieter hat ein eigenes Modul unter `providers/`.
- Tokens immer mit Herkunftslabel: keine falsche Genauigkeit — `tokens_are_real=True` nur wenn `message.usage` vorhanden.

---

## Umgebungsvariablen

| Variable                          | Default                                          | Zweck                          |
|-----------------------------------|--------------------------------------------------|--------------------------------|
| `CLAUDE_PROJECTS_DIR`             | `~/.claude/projects`                             | Claude-Log-Verzeichnis         |
| `CODEX_TRACKER_OBSIDIAN_PROJECTS_DIR` | `C:\Users\walle\Nextcloud2\OBSIDIAN\...` | Obsidian-Export-Basis          |
