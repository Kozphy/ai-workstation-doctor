# AI Workstation Doctor (`awd`)

Windows-first local-AI diagnostics tool. Ships a modular Python CLI with SQLite fact store, the **M1 local AI port checker**, and **redacted shareable Markdown reports**.

The legacy `llama_autostart.py` helper remains for llama.cpp auto-start and richer Windows/GPU scanning until those flows are ported into `awd`.

## Requirements

- Python 3.12+
- Windows recommended (collectors will be Windows-oriented; tests run cross-platform)

## Install

```bash
pip install -e ".[dev]"
```

## Commands

```bash
awd scan
awd scan -o workstation-report.md
awd status
awd report
awd report -o workstation-report.md
```

`awd scan` currently collects Python runtime facts and probes common local-AI ports (`9931`, `11434`, `1234`, `3000`, `8080`, `8000`). It warns when no primary runner port (llama.cpp / Ollama / LM Studio) is open.

Markdown reports (`awd scan -o …` / `awd report`) redact username, home/profile paths, and hostname so you can share them when asking for help.

Database default: `~/.awd/awd.db`  
Override with `--db path\to\file.db`.

## Project layout

```text
src/awd/
  cli/          # awd scan | report | status
  app/          # use-cases + DI container
  domain/       # models + Protocol interfaces
  collectors/   # read-only probes (python, ports)
  checks/       # diagnostic evaluations
  rules/        # dependency-aware check engine
  reports/      # Redacted Markdown writer
  database/     # SQLite schema + FactStore
tests/
docs/ARCHITECTURE.md
docs/GAP_ANALYSIS.md
docs/STRATEGY.md
```

## Development

```bash
pytest
python -m awd scan --db %TEMP%\awd-dev.db
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for layering, schema, interfaces, and Rust-migration notes.  
See [docs/GAP_ANALYSIS.md](docs/GAP_ANALYSIS.md) for roadmap coverage vs `STRATEGY.md`.

## Privacy

Scans and reports are local-only. Nothing is sent off-device.

Shareable reports replace local identity with placeholders (`<user>`, `<userprofile>`, `<home>`, `<host>`). Raw facts remain in the local SQLite DB for `awd status`; only rendered Markdown is redacted.
