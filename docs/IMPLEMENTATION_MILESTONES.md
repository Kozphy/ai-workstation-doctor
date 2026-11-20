# AI Workstation Doctor Implementation Milestones

This plan converts the 12-month roadmap in `STRATEGY.md` into independently testable delivery gates. The strategy's revenue, download, and customer targets are estimates, not evidence that a feature works.

## Evidence model and operating rules

The strategy does not define the labels "Modular Evidence Framework L1-L5". For this repository, use the following operational mapping; it is a project convention, not a claim about an external standard.

| Level | Evidence required | Example |
| --- | --- | --- |
| L1 - Traceability | A strategy requirement maps to a stable fact/check ID and measurable acceptance criterion. | `system.windows_probe` reports whether the Windows probe succeeded. |
| L2 - Component | Reproducible unit tests cover successful results, invalid input, unavailable tools, and timeouts with injected dependencies. | Mocked PowerShell success, timeout, missing executable, and malformed JSON. |
| L3 - Integration | A CLI scan persists facts/findings and produces a redacted report using a temporary database. | `awd scan --db <temp>` emits `system.*` and `ports.*` facts. |
| L4 - CI | The same test command passes on Windows and Ubuntu with Python 3.12 and 3.14. | GitHub Actions matrix, no machine-specific services or secrets. |
| L5 - Field evidence | A real Windows run is compared to observable machine state; report any hardware/driver/API limitations. | Compare CPU/GPU/memory facts to Windows system information and local port listeners. |

No evidence level substitutes for another. CI cannot prove that a probe accurately reflects a user's GPU, and mocked tests cannot prove the user's llama.cpp installation works.

### Approval and autonomy gates

- M1 is the only implementation scope authorized in this task. M2 needs separate user approval after M1 acceptance evidence is reported.
- No repair, privilege elevation, service mutation, network transmission, commit, push, or deployment is included in M1.
- Before any Ralph-style or other autonomous coding loop: M1 must meet L1-L4, the user must review L5 field evidence, and the user must explicitly approve the loop's scope and budget.
- A future loop is limited to three iterations per approved milestone. Each iteration handles one acceptance gap, runs the relevant tests, and stops when criteria pass, three iterations are used, tests remain failing after a repair attempt, or any unsafe/out-of-scope change is needed.
- No autonomous commit, push, deployment, repair, or elevated action is permitted without separate explicit approval.

## Milestones

| Milestone | Roadmap | Independently testable deliverable and acceptance criteria | Approval gate |
| --- | --- | --- | --- |
| M1 - Python workstation prototype | Month 1 | `awd scan` collects Python and Windows OS/CPU/memory/GPU/disk/CUDA-tool facts, probes all six documented local-AI ports, stores results, and writes a redacted report. Windows and `nvidia-smi` probes have explicit timeouts; missing tools, unsupported platforms, command failures, malformed output, and timeouts produce visible status/findings. The existing `llama_autostart.py` remains the llama.cpp lifecycle manager. CI and all tests pass; a real Windows scan is separately reviewed. | M1 tests/CI and L5 evidence before M2. |
| M2 - Runner MVP | Month 2 | Ollama service/process/config/API detection; stable IDs; a documented catalog of approximately 25 independently testable checks; redacted Markdown output. Each check has success and relevant failure fixtures. | User reviews privacy, report output, and M1 field evidence before implementation. |
| M3 - Demand and architecture gate | Month 3 | Signature KB with 50 fixtures; prototype-to-rewrite parity suite. Rust/Tauri work is not started unless the demand gate is met and approved. | Strategy's 300-download threshold is a decision signal, not proof of product-market fit; require user approval to rewrite. |
| M4 - Safe repair foundation | Month 4 | Five repair plans with dry-run diffs, per-action consent, snapshots, verification, rollback, and failure-injection tests. No repair can execute an arbitrary shell command. | Separate security review and explicit approval before enabling any host mutation or elevation. |
| M5 - Pro surface | Month 5 | Dashboard v1 and 15 repair definitions; feature entitlements tested; local operation remains available without account/network dependency. | User approval for licensing, update, and telemetry choices. |
| M6 - Local analysis | Month 6 | Local-LLM log analysis and model-fit advice with schema validation, evidence citations, confidence calibration, and tests proving no off-device request by default. | Explicit approval for any cloud fallback design; no data leaves the device by default. |
| M7 - Additional runtimes | Month 7 | LM Studio, OpenWebUI, Docker/WSL adapters plus reproducible benchmark fixtures; each adapter reports unavailable dependencies without failing unrelated checks. | User approves any optional probes that start containers or consume significant resources. |
| M8 - Community checks | Month 8 | Versioned check-pack schema, compatibility validation, fixture runner, and signed/verified distribution; check packs cannot execute code. | User approval before allowing executable plugins or repairs. |
| M9 - Fleet beta | Month 9 | Opt-in agent inventory and health reporting over outbound authenticated connections; integration tests cover revocation and offline agents. | Separate privacy/security review, design-partner consent, and infrastructure approval. |
| M10 - Remote operations | Month 10 | Remote diagnostics with approval workflow, append-only audit entries, and simulated remediation tests; remote changes require a named approver and rollback. | Explicit per-operation approval; no unattended remediation. |
| M11 - Enterprise deployment | Month 11 | Signed MSI/MSIX build, Intune deployment validation, Entra ID SSO/RBAC tests, and a documented rollback path. | User approves tenant, identity, signing, and deployment targets before provisioning or release. |
| M12 - Self-hosted enterprise | Month 12 | Self-hosted server setup, SIEM export contract tests, backup/restore test, and a SOC 2 readiness gap assessment. | Separate security and operational approval before publishing or deploying a service. |

## M1 acceptance checklist

- [x] Existing `awd` port catalog has six stable ports and bounded TCP probes.
- [x] Existing Markdown writer redacts host identity and local paths.
- [x] Add Windows hardware/CUDA facts to the modular scan with explicit unsupported/error states and bounded subprocess timeouts.
- [x] CI runs the same suite on Windows and Ubuntu, Python 3.12 and 3.14.
- [x] Default test discovery includes legacy helper tests.
- [ ] L5: Run `awd scan` on the target Windows workstation and compare hardware facts and port states to the local machine. This is a user review gate; CI does not satisfy it.
- [ ] L5: Exercise llama.cpp `start/status/stop` with the user's installed version. Do not execute lifecycle commands as part of the scan or CI.

M1 functional checks never install software or mutate system configuration. Existing explicit manager commands remain separate from the scan. Future work must close any discovered lifecycle safety gaps before enabling autonomous implementation.
