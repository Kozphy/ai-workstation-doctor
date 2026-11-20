"""Unit tests for port checker evaluations."""

from __future__ import annotations

from awd.checks.ports import AnyPrimaryRunnerPortCheck, PortCatalogCheck
from awd.domain.enums import FindingStatus
from awd.domain.models import Fact


def _port_facts(*, primary_any_open: bool, open_ports: list[int]) -> dict[str, Fact]:
    results = [
        {
            "port": 9931,
            "name": "llama_cpp",
            "open": 9931 in open_ports,
            "primary": True,
        },
        {
            "port": 11434,
            "name": "ollama",
            "open": 11434 in open_ports,
            "primary": True,
        },
        {
            "port": 1234,
            "name": "lm_studio",
            "open": 1234 in open_ports,
            "primary": True,
        },
        {
            "port": 3000,
            "name": "open_webui",
            "open": 3000 in open_ports,
            "primary": False,
        },
    ]
    return {
        "ports.primary_any_open": Fact(
            key="ports.primary_any_open",
            value=primary_any_open,
            source="test",
        ),
        "ports.primary_open": Fact(
            key="ports.primary_open",
            value=[p for p in open_ports if p in {9931, 11434, 1234}],
            source="test",
        ),
        "ports.results": Fact(key="ports.results", value=results, source="test"),
    }


def test_any_primary_passes_when_ollama_open() -> None:
    result = AnyPrimaryRunnerPortCheck().evaluate(
        _port_facts(primary_any_open=True, open_ports=[11434])
    )
    assert result.finding.status == FindingStatus.PASS
    assert result.finding.check_id == "ports.any_primary_runner"


def test_any_primary_warns_when_none_open() -> None:
    result = AnyPrimaryRunnerPortCheck().evaluate(
        _port_facts(primary_any_open=False, open_ports=[])
    )
    assert result.finding.status == FindingStatus.WARN
    assert "No primary" in result.finding.message


def test_catalog_summarizes_open_count() -> None:
    result = PortCatalogCheck().evaluate(
        _port_facts(primary_any_open=True, open_ports=[11434, 3000])
    )
    assert result.finding.status == FindingStatus.PASS
    assert "2/4" in result.finding.message


def test_any_primary_errors_without_facts() -> None:
    result = AnyPrimaryRunnerPortCheck().evaluate({})
    assert result.finding.status == FindingStatus.ERROR
