"""PII / path redaction for shareable diagnostic reports.

Ports the proven rules from legacy ``llama_autostart.redact`` into a
testable, injectable profile so Markdown reports can leave the machine safely.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RedactionProfile:
    """Secrets and paths to scrub from shareable text.

    Longer values are applied first so ``C:\\Users\\alice`` is replaced before
    ``alice``.
    """

    username: str | None = None
    user_profile: str | None = None
    home: str | None = None
    host_name: str | None = None
    extra_replacements: tuple[tuple[str, str], ...] = ()

    @classmethod
    def from_environment(cls) -> RedactionProfile:
        username = (
            os.environ.get("USERNAME")
            or os.environ.get("USER")
            or os.environ.get("LOGNAME")
        )
        user_profile = os.environ.get("USERPROFILE")
        home = os.environ.get("HOME") or (str(Path.home()) if Path.home() else None)
        host_name = os.environ.get("COMPUTERNAME") or platform.node() or None
        return cls(
            username=_nonempty(username),
            user_profile=_nonempty(user_profile),
            home=_nonempty(home),
            host_name=_nonempty(host_name),
        )


def redact_text(text: str, profile: RedactionProfile | None = None) -> str:
    """Return ``text`` with local identity tokens replaced by placeholders."""
    active = profile or RedactionProfile.from_environment()
    redacted = text

    replacements: list[tuple[str, str]] = []
    if active.user_profile:
        replacements.append((active.user_profile, "<userprofile>"))
    if active.home and active.home != active.user_profile:
        replacements.append((active.home, "<home>"))
    if active.username:
        replacements.append((active.username, "<user>"))
    if active.host_name:
        replacements.append((active.host_name, "<host>"))
    replacements.extend(active.extra_replacements)

    # Longest first avoids partial overwrites (path before username).
    replacements.sort(key=lambda pair: len(pair[0]), reverse=True)

    for original, placeholder in replacements:
        if not original:
            continue
        redacted = _replace_ci_pathish(redacted, original, placeholder)

    return redacted


def _nonempty(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _replace_ci_pathish(text: str, original: str, placeholder: str) -> str:
    """Replace ``original`` case-sensitively, plus a normalized path variant.

    Windows paths often appear with mixed separators; we also try ``/`` vs ``\\``.
    """
    result = text.replace(original, placeholder)
    alt_slash = original.replace("\\", "/")
    if alt_slash != original:
        result = result.replace(alt_slash, placeholder)
    alt_backslash = original.replace("/", "\\")
    if alt_backslash != original:
        result = result.replace(alt_backslash, placeholder)
    return result
