# AI Workstation Doctor / LlamaAutoStart

A Windows-first local-AI diagnostics tool and llama.cpp manager. It starts llama.cpp's server automatically and hidden at logon, scans common local-AI dependencies, checks ports and runner endpoints, and creates a shareable Markdown report.

Requires Windows, Python 3.8+ (standard library only), and `llama` on PATH (`winget install ggml.llamacpp`).

## llama.cpp commands

```text
python llama_autostart.py install    # start automatically at every logon
python llama_autostart.py start      # start now, hidden
python llama_autostart.py status     # task and server state
python llama_autostart.py stop       # stop the server
python llama_autostart.py uninstall  # turn auto-start off
```

## Diagnostics

```text
python llama_autostart.py scan
python llama_autostart.py scan --format json
python llama_autostart.py scan --output workstation-report.md
python llama_autostart.py scan --format json --output workstation-report.json
```

The scan detects Windows hardware, GPU/CUDA tools, llama.cpp, Ollama, LM Studio, OpenWebUI, vLLM, and common local-AI ports. It also detects Ollama Windows services, running processes, environment variables, model directories, and active models. Reports are redacted for the Windows username and user profile.

The llama.cpp server listens on http://127.0.0.1:9931 and writes to `llama-server.log` next to the script. Diagnostic reports are local-only and are never sent anywhere.
