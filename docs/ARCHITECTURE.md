# AI Workstation Doctor — Architecture (Foundation)

This document describes the **Python foundation** plus the first M1 content slice (local AI port checker). GPU/runner managers, repairs, and a Rust core remain deferred.

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
  collectors/    # PythonRuntimeCollector, LocalAiPortsCollector
  checks/        # PythonVersionCheck, port catalog / any-primary-runner
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
2. **Collector** `ports.local_ai` — TCP probe of common local-AI ports (M1 port checker)
3. **Check** `python.version.min` — requires Python ≥ 3.12
4. **Check** `ports.catalog` — summarizes open/closed catalog ports
5. **Check** `ports.any_primary_runner` — WARN if llama.cpp / Ollama / LM Studio ports are all closed
6. **Engine** — dependency-aware evaluation (skip children when parents fail)
7. **Report** — Redacted Markdown summary of findings + fact table (shareable)

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

- WMI / NVML / CUDA collectors in `awd` (still available via legacy `llama_autostart.py scan`)
- HTTP runner health probes, Ollama / llama.cpp managers under `awd`
- YAML check packs / WASM plugins
- Repair planner and elevated helper
- Tauri UI / fleet agent

Next increments: system/GPU facts, then runner HTTP probes, then managers — still behind the same Protocol ports. See `docs/GAP_ANALYSIS.md`.

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
