# LlamaAutoStart

Starts llama.cpp's `llama server` automatically and hidden every time you log in to Windows, so you don't have to run it by hand.

Requires Windows, Python 3.8+ (standard library only), and `llama` on PATH (`winget install ggml.llamacpp`).

```
python llama_autostart.py install    # start automatically at every logon
python llama_autostart.py start      # start now, hidden
python llama_autostart.py status     # task and server state
python llama_autostart.py stop       # stop the server
python llama_autostart.py uninstall  # turn auto-start off
```

The server listens on http://127.0.0.1:9931 and writes its output to `llama-server.log` next to the script.
