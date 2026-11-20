"""Local AI port checker — TCP probes for common runner endpoints.

Ports and names match the M1 roadmap / legacy ``llama_autostart`` scanner.
Conflict *resolution* is intentionally out of scope (checker only).
"""

from __future__ import annotations

import socket
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from awd.domain.models import Fact

ProbeFn = Callable[[str, int, float], bool]


@dataclass(frozen=True, slots=True)
class PortDefinition:
    """Stable catalog entry for a well-known local-AI port."""

    port: int
    name: str
    primary_runner: bool


# Shared with checks — keep IDs/names stable for docs and Rust migration.
LOCAL_AI_PORTS: tuple[PortDefinition, ...] = (
    PortDefinition(9931, "llama_cpp", True),
    PortDefinition(11434, "ollama", True),
    PortDefinition(1234, "lm_studio", True),
    PortDefinition(3000, "open_webui", False),
    PortDefinition(8080, "http_alt", False),
    PortDefinition(8000, "vllm", False),
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_TIMEOUT_S = 0.35


def tcp_port_open(host: str, port: int, timeout: float = DEFAULT_TIMEOUT_S) -> bool:
    """Return True when a TCP connect to ``host:port`` succeeds."""
    with socket.socket() as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


class LocalAiPortsCollector:
    """Read-only TCP probe of common local-AI listener ports."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        timeout: float = DEFAULT_TIMEOUT_S,
        ports: Sequence[PortDefinition] = LOCAL_AI_PORTS,
        probe: ProbeFn | None = None,
    ) -> None:
        self._host = host
        self._timeout = timeout
        self._ports = tuple(ports)
        self._probe: ProbeFn = probe or tcp_port_open

    @property
    def collector_id(self) -> str:
        return "ports.local_ai"

    def collect(self) -> Sequence[Fact]:
        source = self.collector_id
        results: list[dict[str, object]] = []
        open_ports: list[int] = []
        primary_open: list[int] = []

        for definition in self._ports:
            is_open = self._probe(self._host, definition.port, self._timeout)
            results.append(
                {
                    "port": definition.port,
                    "name": definition.name,
                    "open": is_open,
                    "primary": definition.primary_runner,
                }
            )
            if is_open:
                open_ports.append(definition.port)
                if definition.primary_runner:
                    primary_open.append(definition.port)

        return (
            Fact(key="ports.host", value=self._host, source=source),
            Fact(key="ports.results", value=results, source=source),
            Fact(key="ports.open", value=open_ports, source=source),
            Fact(
                key="ports.primary_open",
                value=primary_open,
                source=source,
            ),
            Fact(
                key="ports.primary_any_open",
                value=bool(primary_open),
                source=source,
            ),
        )
