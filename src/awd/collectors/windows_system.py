"""Read-only Windows hardware and CUDA-tool discovery."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from collections.abc import Callable, Sequence
from typing import Any

from awd.domain.models import Fact

PROBE_TIMEOUT_S = 5.0
NVIDIA_SMI_TIMEOUT_S = 2.0
CREATE_NO_WINDOW = 0x08000000

_POWERSHELL_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
try {
  $os = Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption, Version, OSArchitecture
  $memory = Get-CimInstance Win32_OperatingSystem |
    Select-Object TotalVisibleMemorySize, FreePhysicalMemory
  $cpu = @(Get-CimInstance Win32_Processor |
    Select-Object Name, NumberOfCores, NumberOfLogicalProcessors)
  $gpu = @(Get-CimInstance Win32_VideoController |
    Select-Object Name, AdapterRAM, DriverVersion)
  $disks = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID, Size, FreeSpace)
  [ordered]@{
    os = $os
    memory = $memory
    cpu = $cpu
    gpu = $gpu
    disks = $disks
  } | ConvertTo-Json -Depth 4 -Compress
} catch {
  [Console]::Error.WriteLine($_.Exception.Message)
  exit 1
}
"""

CommandRunner = Callable[[list[str], float], subprocess.CompletedProcess[str]]


class WindowsSystemCollector:
    """Collect Windows OS, CPU, memory, GPU, disk, and CUDA-tool facts."""

    def __init__(
        self,
        *,
        platform_name: str | None = None,
        executable_lookup: Callable[[str], str | None] | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._platform_name = platform_name or platform.system()
        self._executable_lookup = executable_lookup or shutil.which
        self._command_runner = command_runner or self._run_command

    @property
    def collector_id(self) -> str:
        return "system.windows"

    def collect(self) -> Sequence[Fact]:
        facts: list[Fact] = [
            Fact(
                key="cuda.path",
                value=os.environ.get("CUDA_PATH"),
                source=self.collector_id,
            ),
            Fact(
                key="cuda.nvidia_smi",
                value=self._executable_lookup("nvidia-smi"),
                source=self.collector_id,
            ),
            Fact(
                key="cuda.nvcc",
                value=self._executable_lookup("nvcc"),
                source=self.collector_id,
            ),
        ]

        if self._platform_name != "Windows":
            facts.extend(self._status_facts(
                "unsupported",
                f"Windows hardware probes are not supported on {self._platform_name}.",
            ))
            return tuple(facts)

        powershell = self._executable_lookup("powershell") or self._executable_lookup("pwsh")
        if powershell is None:
            facts.extend(self._status_facts(
                "error",
                "PowerShell was not found; Windows hardware facts could not be collected.",
            ))
            return tuple(facts)

        try:
            result = self._command_runner(
                [
                    powershell,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    _POWERSHELL_SCRIPT,
                ],
                PROBE_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            facts.extend(self._status_facts(
                "error",
                f"Windows hardware probe exceeded {PROBE_TIMEOUT_S:g} seconds.",
            ))
            return tuple(facts)
        except OSError as exc:
            facts.extend(self._status_facts(
                "error",
                f"Could not run PowerShell hardware probe: {exc}",
            ))
            return tuple(facts)

        if result.returncode != 0:
            detail = result.stderr.strip() or f"PowerShell exited with code {result.returncode}."
            facts.extend(self._status_facts("error", detail))
            return tuple(facts)

        try:
            payload: Any = json.loads(result.stdout)
            self._validate_payload(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            facts.extend(self._status_facts(
                "error",
                f"PowerShell returned invalid hardware data: {exc}",
            ))
            return tuple(facts)

        facts.extend(self._status_facts("ok", None))
        for name in ("os", "memory", "cpu", "gpu", "disks"):
            facts.append(
                Fact(
                    key=f"system.{name}",
                    value=payload[name],
                    source=self.collector_id,
                )
            )
        nvidia_smi = self._executable_lookup("nvidia-smi")
        if nvidia_smi is not None:
            facts.extend(self._collect_nvidia_smi(nvidia_smi))
        return tuple(facts)

    def _collect_nvidia_smi(self, executable: str) -> list[Fact]:
        try:
            result = self._command_runner(
                [
                    executable,
                    "--query-gpu=name,driver_version,memory.total,memory.free",
                    "--format=csv,noheader,nounits",
                ],
                NVIDIA_SMI_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return [
                Fact(
                    key="cuda.nvidia_smi_status",
                    value="error",
                    source=self.collector_id,
                ),
                Fact(
                    key="cuda.nvidia_smi_error",
                    value=f"nvidia-smi exceeded {NVIDIA_SMI_TIMEOUT_S:g} seconds.",
                    source=self.collector_id,
                ),
            ]
        except OSError as exc:
            return [
                Fact(key="cuda.nvidia_smi_status", value="error", source=self.collector_id),
                Fact(key="cuda.nvidia_smi_error", value=str(exc), source=self.collector_id),
            ]

        if result.returncode != 0:
            detail = result.stderr.strip() or f"nvidia-smi exited with code {result.returncode}."
            return [
                Fact(key="cuda.nvidia_smi_status", value="error", source=self.collector_id),
                Fact(key="cuda.nvidia_smi_error", value=detail, source=self.collector_id),
            ]

        return [
            Fact(key="cuda.nvidia_smi_status", value="ok", source=self.collector_id),
            Fact(
                key="cuda.nvidia_smi_output",
                value=result.stdout.strip(),
                source=self.collector_id,
            ),
        ]

    @staticmethod
    def _validate_payload(payload: Any) -> None:
        if not isinstance(payload, dict):
            raise ValueError("expected a JSON object")
        expected = {
            "os": dict,
            "memory": dict,
            "cpu": list,
            "gpu": list,
            "disks": list,
        }
        for key, expected_type in expected.items():
            if not isinstance(payload.get(key), expected_type):
                raise ValueError(f"field {key!r} is missing or has the wrong type")

    def _status_facts(self, status: str, error: str | None) -> list[Fact]:
        facts = [
            Fact(
                key="system.probe_status",
                value=status,
                source=self.collector_id,
            )
        ]
        if error is not None:
            facts.append(
                Fact(
                    key="system.probe_error",
                    value=error,
                    source=self.collector_id,
                )
            )
        return facts

    @staticmethod
    def _run_command(
        args: list[str],
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
            check=False,
        )
