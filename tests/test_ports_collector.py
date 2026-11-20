"""Unit tests for LocalAiPortsCollector."""

from __future__ import annotations

from awd.collectors.ports import LOCAL_AI_PORTS, LocalAiPortsCollector


def test_collects_expected_keys_with_injected_probe() -> None:
    open_set = {11434, 3000}

    def probe(host: str, port: int, timeout: float) -> bool:
        assert host == "127.0.0.1"
        assert timeout > 0
        return port in open_set

    facts = {f.key: f for f in LocalAiPortsCollector(probe=probe).collect()}
    assert facts["ports.host"].value == "127.0.0.1"
    assert facts["ports.open"].value == [11434, 3000]
    assert facts["ports.primary_open"].value == [11434]
    assert facts["ports.primary_any_open"].value is True
    assert len(facts["ports.results"].value) == len(LOCAL_AI_PORTS)
    assert facts["ports.results"].source == "ports.local_ai"


def test_primary_any_open_false_when_all_closed() -> None:
    facts = {
        f.key: f
        for f in LocalAiPortsCollector(probe=lambda _h, _p, _t: False).collect()
    }
    assert facts["ports.open"].value == []
    assert facts["ports.primary_any_open"].value is False
