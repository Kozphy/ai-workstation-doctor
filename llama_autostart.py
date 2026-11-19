"""Start llama.cpp's `llama server` automatically and hidden at Windows logon.

Usage:
    python llama_autostart.py install    # register the logon task
    python llama_autostart.py uninstall  # remove the logon task
    python llama_autostart.py start      # start the server now, hidden
    python llama_autostart.py stop       # stop the running server
    python llama_autostart.py status     # show task and server state

Standard library only. Windows only.
"""
from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
from pathlib import Path

TASK_NAME = "LlamaServerAutoStart"
HOST, PORT = "127.0.0.1", 9931
HERE = Path(__file__).resolve().parent
LOG_FILE = HERE / "llama-server.log"
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008


def find_llama() -> str:
    path = shutil.which("llama")
    if not path:
        sys.exit("Could not find `llama` on PATH. Install it with: winget install ggml.llamacpp")
    return path


def port_open() -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex((HOST, PORT)) == 0


def powershell(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, creationflags=CREATE_NO_WINDOW,
    )


def pythonw() -> str:
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.exists() else exe)


def cmd_start(_: argparse.Namespace) -> None:
    if port_open():
        print(f"llama server is already running on http://{HOST}:{PORT}")
        return
    log = open(LOG_FILE, "ab")
    subprocess.Popen(
        [find_llama(), "server"], stdout=log, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, cwd=HERE,
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS, close_fds=True,
    )
    print(f"Started llama server in the background. Log: {LOG_FILE}")


def cmd_stop(_: argparse.Namespace) -> None:
    r = subprocess.run(["taskkill", "/IM", "llama.exe", "/F"], capture_output=True, text=True)
    print("Stopped llama server." if r.returncode == 0 else "llama server was not running.")


def cmd_install(_: argparse.Namespace) -> None:
    find_llama()
    script = str(Path(__file__).resolve())
    ps = f"""
$a = New-ScheduledTaskAction -Execute '{pythonw()}' -Argument '"{script}" start' -WorkingDirectory '{HERE}'
$t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
$p = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $a -Trigger $t -Settings $s -Principal $p -Description 'Starts llama server in the background at logon' -Force | Out-Null
"""
    r = powershell(ps)
    if r.returncode != 0:
        sys.exit(f"Failed to register task:\n{r.stderr}")
    print(f"Installed. llama server will start hidden at every logon (task '{TASK_NAME}').")


def cmd_uninstall(_: argparse.Namespace) -> None:
    powershell(f"Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false -ErrorAction SilentlyContinue")
    print(f"Removed task '{TASK_NAME}'. A running server keeps running; use `stop` to end it.")


def cmd_status(_: argparse.Namespace) -> None:
    r = powershell(f"(Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue).State")
    state = r.stdout.strip() or "not installed"
    print(f"Logon task: {state}")
    print(f"Server: {'running' if port_open() else 'not running'} at http://{HOST}:{PORT}")


def main() -> None:
    if sys.platform != "win32":
        sys.exit("This tool only runs on Windows.")
    parser = argparse.ArgumentParser(description="Auto-start llama server at Windows logon.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in [("install", cmd_install), ("uninstall", cmd_uninstall),
                     ("start", cmd_start), ("stop", cmd_stop), ("status", cmd_status)]:
        sub.add_parser(name).set_defaults(func=fn)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
