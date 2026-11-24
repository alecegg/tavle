"""Pure checks and assets exported by the page server parts."""

from __future__ import annotations

from pathlib import Path

from varde.pages.server_parts import (
    SECURITY_HEADERS,
    Broadcaster,
    file_signature,
    host_allowed,
    new_token,
    origin_allowed,
    token_matches,
)

ORIGINS = {"http://127.0.0.1:8000"}


def test_tokens_are_unique_and_compared_exactly() -> None:
    token = new_token()
    assert token != new_token()
    assert token_matches(token, token)
    assert not token_matches(None, token)
    assert not token_matches(token + "x", token)


def test_host_check_is_case_insensitive_and_exact() -> None:
    hosts = {"127.0.0.1:8000"}
    assert host_allowed("127.0.0.1:8000", hosts)
    assert host_allowed("127.0.0.1:8000".upper(), hosts)
    assert not host_allowed("evil.example", hosts)
    assert not host_allowed(None, hosts)


def test_origin_check() -> None:
    assert origin_allowed("http://127.0.0.1:8000", ORIGINS)
    assert not origin_allowed("http://evil.example", ORIGINS)
    assert not origin_allowed(None, ORIGINS)


def test_security_headers_lock_down_framing() -> None:
    assert "frame-ancestors 'none'" in SECURITY_HEADERS["Content-Security-Policy"]


def test_broadcaster_publish_and_stop() -> None:
    broadcaster = Broadcaster()
    assert broadcaster.wait(0, 0.01) == (0, False)
    broadcaster.publish()
    assert broadcaster.wait(0, 0.01) == (1, False)
    broadcaster.stop()
    assert broadcaster.wait(1, 0.01) == (1, True)


def test_file_signature_changes_with_content(tmp_path: Path) -> None:
    path = tmp_path / "a.md"
    assert file_signature(path) is None
    path.write_text("a", encoding="utf-8")
    first = file_signature(path)
    path.write_text("ab", encoding="utf-8")
    assert first is not None
    assert file_signature(path) != first
