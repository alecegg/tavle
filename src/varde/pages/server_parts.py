"""Reusable parts of the loopback page server: checks, headers, live updates, assets."""

from __future__ import annotations

import hmac
import secrets
import threading
from collections.abc import Collection, Sequence
from io import BufferedIOBase
from pathlib import Path

from varde.ui.shell import TOKENS_CSS, UI_STATIC

VENDOR_ASSETS = frozenset({"mithril.js"})
MAX_BODY = 64 * 1024
MAX_STREAMS = 16
READ_TIMEOUT = 10
POLL_SECONDS = 0.5
HEARTBEAT_SECONDS = 15
# A header name, not a credential.
TOKEN_HEADER = "X-Varde-Token"  # mollify: ignore[hardcoded-secret]  # noqa: S105
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'self'; script-src 'self'; "
        "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}


def new_token() -> str:
    return secrets.token_urlsafe(24)


def token_matches(sent: str | None, token: str) -> bool:
    return hmac.compare_digest((sent or "").encode(), token.encode())


def origin_allowed(origin: str | None, origins: Collection[str]) -> bool:
    return origin in origins


def host_allowed(host: str | None, hosts: Collection[str]) -> bool:
    return (host or "").lower() in hosts


def is_json_type(content_type: str | None) -> bool:
    if content_type is None:
        return False
    media, _, params = content_type.partition(";")
    if media.strip().lower() != "application/json":
        return False
    return params.strip().lower() in {"", "charset=utf-8"}


def vendor_asset(name: str) -> bytes:
    """Bytes of a vendored script; any name off the allowlist raises ValueError."""
    if name not in VENDOR_ASSETS:
        raise ValueError(f"unknown vendor asset: {name!r}")
    return UI_STATIC.joinpath("vendor", name).read_bytes()


def token_css() -> str:
    return UI_STATIC.joinpath("css", TOKENS_CSS).read_text(encoding="utf-8")


class Broadcaster:
    """Version counter that SSE handlers wait on; stop wakes them all."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._version = 0
        self._stopped = False

    @property
    def version(self) -> int:
        with self._cond:
            return self._version

    def publish(self) -> None:
        with self._cond:
            self._version += 1
            self._cond.notify_all()

    def stop(self) -> None:
        with self._cond:
            self._stopped = True
            self._cond.notify_all()

    def wait(self, seen: int, timeout: float) -> tuple[int, bool]:
        """Wait for a version past `seen`; return (version, stopped)."""
        with self._cond:
            self._cond.wait_for(lambda: self._stopped or self._version != seen, timeout)
            return self._version, self._stopped


def write_event_stream(wfile: BufferedIOBase, broadcaster: Broadcaster) -> None:
    """Send `update` events on each publish and a ping each heartbeat until stopped."""
    seen = broadcaster.version
    try:
        wfile.write(b": connected\n\n")
        wfile.flush()
        while True:
            version, stopped = broadcaster.wait(seen, HEARTBEAT_SECONDS)
            if stopped:
                return
            changed = version != seen
            seen = version
            wfile.write(b"event: update\ndata: {}\n\n" if changed else b": ping\n\n")
            wfile.flush()
    except OSError:
        return


def file_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


def watch_files(
    paths: Sequence[Path], broadcaster: Broadcaster, halt: threading.Event
) -> None:
    """Publish whenever a watched file changes, until `halt` is set."""

    def current() -> list[tuple[int, int] | None]:
        return [file_signature(path) for path in paths]

    seen = current()
    while not halt.wait(POLL_SECONDS):
        latest = current()
        if latest != seen:
            seen = latest
            broadcaster.publish()
