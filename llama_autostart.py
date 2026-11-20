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
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

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


def run_command(args: Iterable[str], timeout: float = 3) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args), capture_output=True, text=True, timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )


def http_status(url: str, timeout: float = 1.5) -> Dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(4096).decode("utf-8", "replace")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = None
            return {"reachable": True, "status": response.status, "body": data}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"reachable": False, "status": None, "error": str(exc)}


def system_facts() -> Dict[str, Any]:
    script = r"""
$facts = [ordered]@{
  computerName = $env:COMPUTERNAME
  os = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue | Select-Object Caption, Version, OSArchitecture)
  memory = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue | Select-Object TotalVisibleMemorySize, FreePhysicalMemory)
  cpu = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors)
  gpu = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Select-Object Name, AdapterRAM, DriverVersion)
  disks = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" -ErrorAction SilentlyContinue | Select-Object DeviceID, Size, FreeSpace)
}
$facts | ConvertTo-Json -Depth 5 -Compress
"""
    r = powershell(script)
    if r.returncode == 0:
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            pass
    return {
        "computerName": os.environ.get("COMPUTERNAME"),
        "cpu": None,
        "gpu": [],
        "memory": None,
        "disks": [],
        "os": None,
    }


def cuda_facts() -> Dict[str, Any]:
    nvidia = shutil.which("nvidia-smi")
    nvcc = shutil.which("nvcc")
    result: Dict[str, Any] = {
        "CUDA_PATH": os.environ.get("CUDA_PATH"),
        "nvidia_smi": nvidia,
        "nvcc": nvcc,
    }
    if nvidia:
        r = run_command([
            nvidia, "--query-gpu=name,driver_version,memory.total,memory.free",
            "--format=csv,noheader,nounits",
        ])
        result["nvidia_smi_output"] = r.stdout.strip() if r.returncode == 0 else r.stderr.strip()
    if nvcc:
        r = run_command([nvcc, "--version"])
        result["nvcc_output"] = r.stdout.strip() if r.returncode == 0 else r.stderr.strip()
    return result


def ollama_api_url(host: str) -> str:
    value = (host or "127.0.0.1:11434").strip()
    if "://" not in value:
        value = "http://" + value
    return value.rstrip("/") + "/api/version"


def probe_runners(ollama_host: str = "127.0.0.1:11434") -> Dict[str, Any]:
    return {
        "llama_cpp": http_status(f"http://{HOST}:{PORT}/health"),
        "ollama": http_status(ollama_api_url(ollama_host)),
        "lm_studio": http_status("http://127.0.0.1:1234/v1/models"),
        "open_webui": http_status("http://127.0.0.1:3000/"),
        "vllm": http_status("http://127.0.0.1:8000/v1/models"),
    }


def ollama_facts() -> Dict[str, Any]:
    script = r"""
$names = @('Ollama', 'OllamaService', 'ollama')
$service = $null
foreach ($name in $names) {
  $candidate = Get-CimInstance Win32_Service -Filter "Name='$name'" -ErrorAction SilentlyContinue
  if ($candidate) { $service = $candidate; break }
  $candidate = Get-Service -Name $name -ErrorAction SilentlyContinue
  if ($candidate) { $service = [pscustomobject]@{ Name=$candidate.Name; State=$candidate.Status.ToString(); StartMode=$null; PathName=$null; ProcessId=$null }; break }
}
$processes = @(Get-CimInstance Win32_Process -Filter "Name='ollama.exe'" -ErrorAction SilentlyContinue |
  Select-Object ProcessId, ExecutablePath)
$facts = [ordered]@{
  service = if ($service) {
    [ordered]@{
      name = $service.Name
      state = $service.State
      start_mode = $service.StartMode
      path = $service.PathName
      process_id = $service.ProcessId
    }
  } else { $null }
  process_running = [bool]($processes.Count)
  processes = @($processes)
  host = [Environment]::GetEnvironmentVariable('OLLAMA_HOST', 'Process')
  if (-not $host) { $host = [Environment]::GetEnvironmentVariable('OLLAMA_HOST', 'User') }
  if (-not $host) { $host = [Environment]::GetEnvironmentVariable('OLLAMA_HOST', 'Machine') }
  models = [Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'Process')
  if (-not $models) { $models = [Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'User') }
  if (-not $models) { $models = [Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'Machine') }
}
$facts | ConvertTo-Json -Depth 5 -Compress
"""
    r = powershell(script)
    facts: Dict[str, Any] = {
        "executable": shutil.which("ollama"),
        "service": None,
        "process_running": False,
        "processes": [],
        "host": os.environ.get("OLLAMA_HOST"),
        "models": os.environ.get("OLLAMA_MODELS"),
        "ps": None,
    }
    if r.returncode == 0:
        try:
            detected = json.loads(r.stdout)
            facts.update(detected)
        except json.JSONDecodeError:
            pass
    if not facts["host"]:
        facts["host"] = "127.0.0.1:11434"

    ollama = facts["executable"]
    if ollama:
        try:
            ps = run_command([ollama, "ps"], timeout=3)
            facts["ps"] = {
                "returncode": ps.returncode,
                "output": ps.stdout.strip(),
                "error": ps.stderr.strip(),
            }
        except (subprocess.TimeoutExpired, OSError) as exc:
            facts["ps"] = {"returncode": None, "output": "", "error": str(exc)}
    return facts


def port_status(host: str = "127.0.0.1", ports: Iterable[int] = (9931, 11434, 1234, 3000, 8080, 8000)):
    result = {}
    for port in ports:
        with socket.socket() as sock:
            sock.settimeout(0.35)
            result[str(port)] = sock.connect_ex((host, port)) == 0
    return result


def scheduled_task_status() -> str:
    r = powershell(
        "(Get-ScheduledTask -TaskName "
        f"'{TASK_NAME}' -ErrorAction SilentlyContinue).State"
    )
    return r.stdout.strip() or "not installed"


def collect_facts() -> Dict[str, Any]:
    ollama = ollama_facts()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": system_facts(),
        "cuda": cuda_facts(),
        "ports": port_status(),
        "runners": probe_runners(ollama.get("host", "127.0.0.1:11434")),
        "ollama": ollama,
        "llama_cpp": {
            "task": scheduled_task_status(),
            "endpoint": f"http://{HOST}:{PORT}",
            "executable": shutil.which("llama"),
            "log": str(LOG_FILE),
        },
    }


def redact(text: str) -> str:
    redacted = text
    username = os.environ.get("USERNAME")
    userprofile = os.environ.get("USERPROFILE")
    if username:
        redacted = redacted.replace(username, "<user>")
    if userprofile:
        redacted = redacted.replace(userprofile, "<userprofile>")
    redacted = redacted.replace(str(HERE), "<app>")
    return redacted


def markdown_report(facts: Dict[str, Any]) -> str:
    host = facts["host"]
    os_info = host.get("os") or {}
    memory = host.get("memory") or {}
    lines = [
        "# AI Workstation Diagnostic Report",
        "",
        f"Generated: {facts['generated_at']}",
        "",
        "## System",
        f"- OS: {redact(str(os_info.get('Caption', 'Unknown')))}",
        f"- Computer: `{redact(str(host.get('computerName', 'Unknown')))}`",
        f"- CPU: {redact(str(host.get('cpu')))}",
        f"- Memory: total {memory.get('TotalVisibleMemorySize', 'unknown')} KB",
        "",
        "## GPU / CUDA",
    ]
    gpu = host.get("gpu") or []
    if isinstance(gpu, dict):
        gpu = [gpu]
    if gpu:
        for item in gpu:
            lines.append(f"- GPU: {redact(str(item))}")
    else:
        lines.append("- No GPU detected through WMI.")
    cuda = facts["cuda"]
    lines.extend([
        f"- NVIDIA-SMI: `{cuda.get('nvidia_smi') or 'not found'}`",
        f"- NVCC: `{cuda.get('nvcc') or 'not found'}`",
        f"- CUDA_PATH: `{redact(str(cuda.get('CUDA_PATH') or 'not set'))}`",
    ])
    if cuda.get("nvidia_smi_output"):
        lines.extend(["", "```text", redact(cuda["nvidia_smi_output"]), "```"])

    lines.extend(["", "## Runner and port status"])
    for port, open_port in facts["ports"].items():
        lines.append(f"- Port {port}: {'open' if open_port else 'closed'}")
    for name, probe in facts["runners"].items():
        lines.append(f"- {name}: {'reachable' if probe['reachable'] else 'not reachable'}")

    ollama = facts.get("ollama")
    if ollama:
        lines.extend(["", "## Ollama"])
        lines.append(f"- Executable: `{redact(str(ollama.get('executable') or 'not found'))}`")
        lines.append(f"- Process running: {'yes' if ollama.get('process_running') else 'no'}")
        service = ollama.get("service")
        if service:
            lines.append(
                "- Windows service: "
                f"`{redact(str(service.get('name', 'unknown')))}` "
                f"(state: {redact(str(service.get('state', 'unknown')))})"
            )
        else:
            lines.append("- Windows service: not registered")
        lines.append(f"- OLLAMA_HOST: `{redact(str(ollama.get('host') or 'not set'))}`")
        lines.append(f"- OLLAMA_MODELS: `{redact(str(ollama.get('models') or 'not set'))}`")
        ps = ollama.get("ps")
        if ps and ps.get("output"):
            lines.extend(["- Active models:", "```text", redact(ps["output"]), "```"])

    lines.extend([
        "",
        "## llama.cpp",
        f"- Executable: `{redact(str(facts['llama_cpp'].get('executable') or 'not found'))}`",
        f"- Scheduled task: {facts['llama_cpp']['task']}",
        f"- Endpoint: {facts['llama_cpp']['endpoint']}",
        f"- Log: `{redact(facts['llama_cpp']['log'])}`",
        "",
        "## Findings",
    ])
    findings = []
    if not cuda.get("nvidia_smi") and any("GPU" in str(item) and "nvidia" in str(item).lower()
                                           for item in gpu):
        findings.append("- `cuda.nvidia_smi_missing`: NVIDIA-SMI was not found.")
    if not facts["ports"]["9931"] and facts["llama_cpp"]["task"] not in ("not installed", "Disabled"):
        findings.append("- `llamacpp.server_stopped`: The scheduled llama.cpp server task is installed but port 9931 is closed.")
    if not any(facts["ports"][str(port)] for port in (11434, 1234, 9931)):
        findings.append("- `runners.none_reachable`: No common local AI runner endpoint is reachable.")
    ollama = facts.get("ollama")
    if ollama:
        ollama_reachable = facts["runners"].get("ollama", {}).get("reachable")
        service = ollama.get("service")
        if not ollama_reachable and (ollama.get("executable") or ollama.get("process_running") or service):
            findings.append(
                "- `ollama.service_stopped`: Ollama is installed or has a process/service, "
                "but the API endpoint is not reachable."
            )
        if ollama_reachable:
            findings.append("- `ollama.service.running`: Ollama API is reachable.")
    lines.extend(findings or ["- No immediate issues detected."])
    return "\n".join(lines) + "\n"


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


def cmd_scan(args: argparse.Namespace) -> None:
    facts = collect_facts()
    if args.format == "json":
        output = json.dumps(facts, indent=2, ensure_ascii=False)
    else:
        output = markdown_report(facts)
    if args.output:
        destination = Path(args.output).expanduser()
        destination.write_text(output, encoding="utf-8")
        print(f"Report saved to: {destination}")
    else:
        print(output, end="")


def main() -> None:
    if sys.platform != "win32":
        sys.exit("This tool only runs on Windows.")
    parser = argparse.ArgumentParser(
        description="AI Workstation Doctor: llama.cpp management and Windows diagnostics."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in [("install", cmd_install), ("uninstall", cmd_uninstall),
                     ("start", cmd_start), ("stop", cmd_stop), ("status", cmd_status),
                     ("scan", cmd_scan)]:
        sub.add_parser(name).set_defaults(func=fn)
    scan = sub.choices["scan"]
    scan.add_argument("--format", choices=("markdown", "json"), default="markdown")
    scan.add_argument("--output", "-o", help="Write the report to a file.")
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
