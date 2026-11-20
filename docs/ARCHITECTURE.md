# AI Workstation Doctor — Architecture (Foundation)

This document describes the **Python foundation** plus the M1 content slice (Windows system probe and local AI port checker). The llama.cpp lifecycle manager remains the legacy `llama_autostart.py` helper. Other runner managers, repairs, and a Rust core remain deferred.

## Goals

| Goal | How the foundation supports it |
| --- | --- |
| Windows-first local AI diagnostics | CLI `awd`; collectors are read-only probes |
| Modular / extensible checks | `Collector` and `Check` protocols; register in `AppContainer` |
| SQLite fact store | Versioned schema in `database/schema.sql` |
| Markdown reporting | `MarkdownReportWriter` |
| Future Rust migration | Domain models + Protocol ports map 1:1 to Rust structs/traits |

## Layering

```text
┌─────────────────────────────────────────────────────────┐
│  cli/          presentation (argparse)                  │
├─────────────────────────────────────────────────────────┤
│  app/          use-cases + composition root (DI)        │
├────────────┬────────────┬────────────┬──────────────────┤
│ collectors │   checks   │   rules    │     reports      │
├────────────┴────────────┴────────────┴──────────────────┤
│  domain/       models + Protocol ports (no I/O)         │
├─────────────────────────────────────────────────────────┤
│  database/     SQLite FactStore adapter                 │
└─────────────────────────────────────────────────────────┘
```

Dependency rule: **inward only**. `domain` never imports adapters. `cli` and `app` wire concrete types.

## Pipeline

```text
awd scan
   │
   ▼
Collectors ──► Facts ──► FactStore (SQLite)
                           │
                           ▼
                    RuleEngine + Checks ──► Findings ──► FactStore
                                                           │
                                                           ▼
                                                    Markdown report
```

`awd status` and `awd report` read the latest session; they do not re-probe the machine.

## Package map

```text
src/awd/
  cli/           # awd scan | report | status
  app/           # ScanService, StatusService, AppContainer
  domain/        # Fact, Finding, ScanSession, Protocols
  collectors/    # PythonRuntimeCollector, LocalAiPortsCollector, WindowsSystemCollector
  checks/        # PythonVersionCheck, WindowsSystemProbeCheck, port checks
  rules/         # SimpleRuleEngine (DAG + skip)
  reports/       # MarkdownReportWriter
  database/      # schema.sql, SqliteFactStore
```

## Core interfaces (Rust migration surface)

| Python Protocol | Responsibility | Likely Rust trait |
| --- | --- | --- |
| `Collector` | Emit JSON-friendly facts | `trait Collector` |
| `Check` | Evaluate facts → finding; declare `depends_on` | `trait Check` |
| `FactStore` | Persist sessions / facts / findings | `trait FactStore` |
| `RuleEngine` | Topo-sort checks; skip failed deps | `trait RuleEngine` |
| `ReportWriter` | Render artifacts | `trait ReportWriter` |

Stable public contracts:

- Check IDs: dotted strings (`python.version.min`)
- Fact keys: dotted strings (`python.version_tuple`)
- Enum string values: `pass|fail|warn|skip|error`, severities, session status
- Timestamps: ISO-8601 UTC in SQLite TEXT columns

## Database schema (v1)

| Table | Purpose |
| --- | --- |
| `schema_migrations` | Applied schema version |
| `scan_sessions` | One row per `awd scan` |
| `facts` | Keyed observations per session (`UNIQUE(session_id, key)`) |
| `findings` | Check outcomes with evidence JSON |

See `src/awd/database/schema.sql`. Keep column names and semantics when porting to Rust (`rusqlite`).

## Dependency injection

`AppContainer.build()` is the composition root. Tests inject a temp DB path and can swap collectors/checks without changing use-cases.

```python
container = AppContainer.build(db_path=tmp_path / "awd.db")
ScanService(
    fact_store=container.fact_store,
    collectors=container.collectors,
    checks=container.checks,
    rule_engine=container.rule_engine,
    report_writer=container.report_writer,
).run()
```

## What ships now

1. **Collector** `python.runtime` — interpreter version, executable, OS identity
2. **Collector** `system.windows` — read-only OS, CPU, memory, GPU, disk, and CUDA-tool facts on Windows
3. **Collector** `ports.local_ai` — bounded TCP probes of common local-AI ports (M1 port checker)
4. **Check** `python.version.min` — requires Python ≥ 3.12
5. **Check** `system.windows_probe` — makes unsupported or failed hardware probes visible
6. **Checks** `ports.catalog`, `ports.any_primary_runner` — summarize ports and warn if all primary runner ports are closed
7. **Engine** — dependency-aware evaluation (skip children when parents fail)
8. **Report** — Redacted Markdown summary of findings + fact table (shareable)

The Windows hardware subprocess has a five-second timeout; the optional `nvidia-smi` probe has a two-second timeout. No scan collector installs software, starts/stops services, or changes host configuration.

### Port catalog (stable)

| Port | Name | Primary runner |
| ---: | --- | --- |
| 9931 | llama_cpp | yes |
| 11434 | ollama | yes |
| 1234 | lm_studio | yes |
| 3000 | open_webui | no |
| 8080 | http_alt | no |
| 8000 | vllm | no |

Conflict *resolution* (kill process / rebind) is not implemented — checker only.

### Report redaction (shareable)

`MarkdownReportWriter` applies `redact_text()` before returning or writing a file. Default profile scrubs:

| Token | Placeholder |
| --- | --- |
| Windows `USERNAME` / Unix `USER` | `<user>` |
| `USERPROFILE` | `<userprofile>` |
| `HOME` / `Path.home()` | `<home>` |
| `COMPUTERNAME` / hostname | `<host>` |

Longer paths are replaced first. Injection via `RedactionProfile` keeps unit tests deterministic. Pass `redact=False` only for local debugging.

## Explicitly deferred

- HTTP runner health probes, Ollama / llama.cpp managers under `awd`
- YAML check packs / WASM plugins
- Repair planner and elevated helper
- Tauri UI / fleet agent

Next increments: Ollama manager and expanded checks, then demand-gated Rust/Tauri work. See `docs/GAP_ANALYSIS.md` and `docs/IMPLEMENTATION_MILESTONES.md`.

## Commands

```bash
pip install -e ".[dev]"
awd scan
awd scan -o workstation-report.md
awd status
awd report
awd report -o report.md
pytest
```
