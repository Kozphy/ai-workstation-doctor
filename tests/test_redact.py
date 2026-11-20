"""Unit tests for shareable-report redaction."""

from __future__ import annotations

from awd.reports.redact import RedactionProfile, redact_text


def test_redacts_username_profile_home_and_host() -> None:
    profile = RedactionProfile(
        username="alice",
        user_profile=r"C:\Users\alice",
        home=r"C:\Users\alice",
        host_name="ALICE-PC",
    )
    raw = (
        r"Host ALICE-PC path C:\Users\alice\AppData\Local\ollama "
        r"user alice executable C:\Users\alice\AppData\Local\Programs\Python\python.exe"
    )
    out = redact_text(raw, profile)
    assert "alice" not in out
    assert "ALICE-PC" not in out
    assert "<host>" in out
    assert "<userprofile>" in out
    assert "<user>" in out
    assert r"C:\Users\alice" not in out


def test_redacts_forward_slash_variant_of_profile() -> None:
    profile = RedactionProfile(
        username="bob",
        user_profile=r"C:\Users\bob",
        home=None,
        host_name=None,
    )
    out = redact_text("models at C:/Users/bob/.ollama", profile)
    assert "bob" not in out
    assert "<userprofile>" in out


def test_longer_paths_win_over_username_substring() -> None:
    profile = RedactionProfile(
        username="sam",
        user_profile=r"D:\Users\sam",
        home=None,
        host_name=None,
    )
    out = redact_text(r"D:\Users\sam\models", profile)
    assert out == r"<userprofile>\models"


def test_extra_replacements() -> None:
    profile = RedactionProfile(
        extra_replacements=((r"C:\apps\awd", "<app>"),),
    )
    assert redact_text(r"log C:\apps\awd\llama-server.log", profile) == (
        r"log <app>\llama-server.log"
    )
