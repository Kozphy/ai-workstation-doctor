# AI Workstation Doctor (`awd`)

**Windows-first diagnostics for local AI.** Find why Ollama, llama.cpp, LM Studio, or OpenWebUI is not responding — ports, GPU/CUDA tools, and system facts — then share a **redacted** Markdown report.

[![CI](https://github.com/Kozphy/ai-workstation-doctor/actions/workflows/tests.yml/badge.svg)](https://github.com/Kozphy/ai-workstation-doctor/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

> Community edition is **free**. Need it installed or fixed on your PC? See [Support & commercial use](docs/SUPPORT.md).

## Why this exists

Local AI fails in the gaps between tools: CUDA missing, wrong port, runner down, GPU idle. AI Workstation Doctor is the reliability layer — diagnose locally, keep data on-device, share a safe report when you need help.

## Quick start

```bash
git clone https://github.com/Kozphy/ai-workstation-doctor.git
cd ai-workstation-doctor
pip install -e ".[dev]"
awd scan -o workstation-report.md
awd status
```

Requirements: **Python 3.12+**. Windows recommended (system/GPU collectors are Windows-oriented; core tests run cross-platform).

## What `awd scan` does today

| Capability | Detail |
| --- | --- |
| Port checker | Probes `9931`, `11434`, `1234`, `3000`, `8080`, `8000` |
| System / GPU | OS, CPU, memory, GPU, disk (Windows); CUDA tools + `nvidia-smi` when present |
| Python baseline | Requires 3.12+ |
| Shareable report | Markdown with `<user>`, `<userprofile>`, `<home>`, `<host>` redaction |
| Local store | SQLite at `~/.awd/awd.db` (override with `--db`) |

```bash
awd scan
awd scan -o workstation-report.md
awd status
awd report
awd report -o workstation-report.md
```

The scanner is **read-only**. For llama.cpp autostart on Windows:

```text
python llama_autostart.py install
python llama_autostart.py start
python llama_autostart.py status
python llama_autostart.py stop
python llama_autostart.py uninstall
```

Requires `llama` on PATH (`winget install ggml.llamacpp`).

## Project layout

```text
src/awd/          # Modular CLI: collectors, checks, SQLite, reports
llama_autostart.py
tests/
docs/
  ARCHITECTURE.md
  GAP_ANALYSIS.md
  STRATEGY.md
  SUPPORT.md
```

## Development

```bash
pytest
python -m awd scan --db %TEMP%\awd-dev.db
```

CI runs on Windows and Ubuntu (Python 3.12 / 3.14).

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Gap analysis vs roadmap](docs/GAP_ANALYSIS.md)
- [Product strategy](docs/STRATEGY.md)
- [Support & commercial use](docs/SUPPORT.md)
- [Implementation milestones](docs/IMPLEMENTATION_MILESTONES.md)

## Privacy

Scans and reports stay on your machine. Nothing is sent off-device. Only rendered Markdown is redacted for sharing; the local DB keeps raw facts for `awd status`.

## License

[MIT](LICENSE) © Kozphy
