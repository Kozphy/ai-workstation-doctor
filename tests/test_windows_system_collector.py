"""Tests for the bounded, read-only Windows hardware collector."""

from __future__ import annotations

import json
import subprocess

from awd.checks.system import WindowsSystemProbeCheck
from awd.collectors.windows_system import (
    NVIDIA_SMI_TIMEOUT_S,
    PROBE_TIMEOUT_S,
    WindowsSystemCollector,
)
from awd.domain.enums import FindingStatus
from awd.domain.models import Fact


def _payload() -> dict[str, object]:
    return {
        "os": {"Caption": "Windows 11", "Version": "10.0", "OSArchitecture": "64-bit"},
        "memory": {"TotalVisibleMemorySize": 16000000, "FreePhysicalMemory": 8000000},
        "cpu": [{"Name": "Test CPU", "NumberOfCores": 8, "NumberOfLogicalProcessors": 16}],
        "gpu": [{"Name": "Test GPU", "AdapterRAM": 8000000000, "DriverVersion": "1.2"}],
        "disks": [{"DeviceID": "C:", "Size": 1000, "FreeSpace": 500}],
    }


def _fact_map(collector: WindowsSystemCollector) -> dict[str, Fact]:
    return {fact.key: fact for fact in collector.collect()}


def test_collects_windows_hardware_and_cuda_paths() -> None:
    calls: list[tuple[list[str], float]] = []

    def runner(args: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        calls.append((args, timeout))
        output = (
            json.dumps(_payload())
            if args[0].endswith("powershell.exe")
            else "Test GPU, 550.1, 8192, 4096"
        )
        return subprocess.CompletedProcess(args, 0, output, "")

    collector = WindowsSystemCollector(
        platform_name="Windows",
        executable_lookup=lambda name: f"C:\\Tools\\{name}.exe",
        command_runner=runner,
    )
    facts = _fact_map(collector)

    assert facts["system.probe_status"].value == "ok"
    assert facts["system.cpu"].value == _payload()["cpu"]
    assert facts["system.gpu"].value == _payload()["gpu"]
    assert facts["system.disks"].value == _payload()["disks"]
    assert facts["cuda.nvidia_smi"].value.endswith("nvidia-smi.exe")
    assert facts["cuda.nvidia_smi_status"].value == "ok"
    assert facts["cuda.nvidia_smi_output"].value == "Test GPU, 550.1, 8192, 4096"
    assert calls[0][1] == PROBE_TIMEOUT_S
    assert calls[1][1] == NVIDIA_SMI_TIMEOUT_S
    assert calls[0][0][1:4] == ["-NoProfile", "-NonInteractive", "-Command"]
    assert "Get-CimInstance" in calls[0][0][4]
    assert calls[1][0][1] == "--query-gpu=name,driver_version,memory.total,memory.free"


def test_non_windows_platform_is_explicitly_unsupported_without_process() -> None:
    def fail_if_called(_args: list[str], _timeout: float) -> subprocess.CompletedProcess[str]:
        raise AssertionError("PowerShell must not run off Windows")

    facts = _fact_map(WindowsSystemCollector(
        platform_name="Linux",
        command_runner=fail_if_called,
    ))

    assert facts["system.probe_status"].value == "unsupported"
    assert "system.os" not in facts


def test_missing_powershell_is_reported() -> None:
    facts = _fact_map(WindowsSystemCollector(
        platform_name="Windows",
        executable_lookup=lambda _name: None,
    ))

    assert facts["system.probe_status"].value == "error"
    assert "PowerShell was not found" in facts["system.probe_error"].value


def test_timeout_is_reported_and_bounded() -> None:
    def timeout(_args: list[str], _timeout: float) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired("powershell", PROBE_TIMEOUT_S)

    facts = _fact_map(WindowsSystemCollector(
        platform_name="Windows",
        executable_lookup=lambda _name: "powershell.exe",
        command_runner=timeout,
    ))

    assert facts["system.probe_status"].value == "error"
    assert "exceeded 5 seconds" in facts["system.probe_error"].value


def test_failed_or_malformed_powershell_output_is_reported() -> None:
    failed = _fact_map(WindowsSystemCollector(
        platform_name="Windows",
        executable_lookup=lambda _name: "powershell.exe",
        command_runner=lambda args, _timeout: subprocess.CompletedProcess(
            args, 1, "", "CIM query failed"
        ),
    ))
    malformed = _fact_map(WindowsSystemCollector(
        platform_name="Windows",
        executable_lookup=lambda _name: "powershell.exe",
        command_runner=lambda args, _timeout: subprocess.CompletedProcess(
            args, 0, '{"os": null}', ""
        ),
    ))

    assert failed["system.probe_status"].value == "error"
    assert failed["system.probe_error"].value == "CIM query failed"
    assert malformed["system.probe_status"].value == "error"
    assert "field 'os'" in malformed["system.probe_error"].value


def test_nvidia_smi_timeout_is_reported_without_failing_system_scan() -> None:
    call_count = 0

    def runner(args: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return subprocess.CompletedProcess(args, 0, json.dumps(_payload()), "")
        raise subprocess.TimeoutExpired(args[0], timeout)

    facts = _fact_map(WindowsSystemCollector(
        platform_name="Windows",
        executable_lookup=lambda name: (
            "C:\\Tools\\powershell.exe"
            if name in ("powershell", "nvidia-smi")
            else None
        ),
        command_runner=runner,
    ))

    assert facts["system.probe_status"].value == "ok"
    assert facts["cuda.nvidia_smi_status"].value == "error"
    assert "exceeded 2 seconds" in facts["cuda.nvidia_smi_error"].value


def test_probe_check_maps_success_warning_and_missing_fact() -> None:
    check = WindowsSystemProbeCheck()
    success = check.evaluate({
        "system.probe_status": Fact("system.probe_status", "ok", "test"),
    })
    unsupported_facts = {
        fact.key: fact
        for fact in WindowsSystemCollector(platform_name="Linux").collect()
    }
    unsupported = check.evaluate(unsupported_facts)
    missing = check.evaluate({})

    assert success.finding.status == FindingStatus.PASS
    assert unsupported.finding.status == FindingStatus.WARN
    assert missing.finding.status == FindingStatus.ERROR
