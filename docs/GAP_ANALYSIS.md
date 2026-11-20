# Gap Analysis — AI Workstation Doctor vs STRATEGY.md (M1–M3)

Date: 2026-11-20 (updated)  
Scope: repository vs Months 1–3 only. Fleet / Enterprise / Month 4+ ignored.

## 1. Gap analysis

| Month | Roadmap item | Status |
| --- | --- | --- |
| M1 | Modular `awd scan` | **Partial** — pipeline + ports; limited system facts |
| M1 | Port checker | **Done** in `awd` |
| M1 | llama.cpp Manager | **Partial** — `llama_autostart.py` only |
| M1 | System / GPU / CUDA scan | **Partial** — legacy only |
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

- System/GPU/CUDA scan (legacy)
- Runner HTTP probing (legacy; TCP ports in `awd`)
- llama.cpp / Ollama managers (legacy)

### Missing (M1–M3, in-scope)

- System/GPU/CUDA collectors in `awd`
- Runner HTTP reachability in `awd`
- llama.cpp + Ollama managers under `awd`
- Broader check pack (~25)
- Rule-based log signatures (MVP listed; higher effort)

## 2. Missing feature ranking (M1–M3 only)

| Feature | User value | Impl. risk | MVP fit |
| --- | --- | --- | --- |
| Redacted shareable Markdown report | High (viral) | **Lowest** | Explicit MVP |
| Runner HTTP reachability | High | Low | Runner detection |
| System / GPU / CUDA scan in `awd` | Very high | Medium (WMI/smi) | Core MVP question |
| llama.cpp Manager → `awd` | High | Low–Med | M1 |
| Ollama Manager | High | Medium | M2 |
| Expand toward 25 checks | High | High | M2 |
| Rule-based log signatures | High | Medium–High | MVP but heavier |

## 3. Implementation proposal (selected)

**Feature:** Redacted shareable Markdown report  

**Why this one:** STRATEGY MVP rates it High user value / Low complexity / High revenue impact (viral loop). Lowest risk among remaining MVP items (pure text transforms, no OS probes). Makes `awd scan -o report.md` safe to post when seeking help.

**Approach:**

1. `RedactionProfile` + `redact_text()` (username, profile, home, host; longest-first)
2. Apply inside `MarkdownReportWriter` before write/return (on by default)
3. Unit tests with injected profiles; keep `redact=False` for debugging
4. Document privacy behavior in README / ARCHITECTURE / this file

**Out of scope for this change:** system scan, managers, HTTP probes, Fleet, repairs.
