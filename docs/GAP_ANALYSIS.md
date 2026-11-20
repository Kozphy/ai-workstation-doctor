# Gap Analysis — AI Workstation Doctor vs STRATEGY.md (M1–M3)

Date: 2026-11-20  
Scope: repository vs Months 1–3 only. Fleet / Enterprise / Month 4+ ignored.

## 1. Gap analysis

| Month | Roadmap item | Status |
| --- | --- | --- |
| M1 | Modular `awd scan` | **Done** — pipeline, Windows facts, and ports |
| M1 | Port checker | **Done** in `awd` |
| M1 | llama.cpp Manager | **Partial** — `llama_autostart.py` only |
| M1 | System / GPU / CUDA scan | **Done** — read-only WMI facts plus optional `nvidia-smi` |
| M2 | Ollama Manager | **Missing** in `awd` |
| M2 | ~25 checks | **Missing** (few checks today) |
| M2 | Shareable Markdown report | **Done** — redacted reports in `awd` |
| M3 | Rust + Tauri / signature KB | **Deferred** (demand gate) |

### Completed in `awd`

- Clean architecture, DI, SQLite fact store, CLI
- Port checker (`ports.*`)
- Python runtime sample check
- **Redacted shareable Markdown report**

### Partial

- llama.cpp manager remains the legacy standalone helper
- Runner HTTP probing is legacy-only; modular `awd` currently checks TCP ports

### Missing (M1–M3, in-scope)

- Runner HTTP reachability in `awd`
- llama.cpp lifecycle commands under `awd`
- Ollama manager
- Broader check pack (~25)
- Rule-based log signatures (MVP listed; higher effort)

## 2. Verification and approval gates

M1 must pass the Windows/Linux, Python 3.12/3.14 CI matrix and local integration suite. A real Windows scan must also confirm the emitted hardware facts against the machine before M2 is approved. The current collector is read-only; repairs and elevation remain out of scope.

The 12-month milestones, acceptance criteria, project-local L1-L5 evidence mapping, and future approval gates are maintained in [IMPLEMENTATION_MILESTONES.md](IMPLEMENTATION_MILESTONES.md).
