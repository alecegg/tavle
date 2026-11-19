"""Remote access: no key or cookie; Host, Origin, token and --allow-edit guards.

The server binds loopback. `remote = True` simulates a non-loopback policy so no
test binds a Tailscale address.
"""

from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from varde.pages.serve import PageServer, edit_denied

DOC = "# Plan\n\nBody text.\n\n```html\n<p>hi</p>\n```\n"


def start(tmp_path: Path, remote_policy: bool, allow_edit: bool = False):
    doc = tmp_path / "plan.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0, "127.0.0.1", allow_edit)
    server.remote = remote_policy
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def stop(server: PageServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(5)


@pytest.fixture
def remote_server(tmp_path: Path) -> Iterator[PageServer]:
    server, thread = start(tmp_path, True)
    yield server
    stop(server, thread)


@pytest.fixture
def editing_server(tmp_path: Path) -> Iterator[PageServer]:
    server, thread = start(tmp_path, True, allow_edit=True)
    yield server
    stop(server, thread)


@pytest.fixture
def loopback_server(tmp_path: Path) -> Iterator[PageServer]:
    server, thread = start(tmp_path, False)
    yield server
    stop(server, thread)


def request(
    srv: PageServer,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    token: bool = True,
) -> tuple[int, dict[str, str], bytes]:
    host = f"127.0.0.1:{srv.port}"
    headers = {"Host": host, **(headers or {})}
    payload = None
    if method == "POST":
        headers.setdefault("Origin", f"http://{host}")
        headers["Content-Type"] = "application/json"
        if token:
            headers["X-Varde-Token"] = srv.token
        payload = json.dumps(body or {})
    conn = http.client.HTTPConnection("127.0.0.1", srv.port, timeout=5)
    conn.request(method, path, payload, headers)
    response = conn.getresponse()
    data = response.read() if path != "/events" else b""
    out = (response.status, {k.lower(): v for k, v in response.getheaders()}, data)
    conn.close()
    return out


@pytest.mark.parametrize("path", ["/", "/block?anchor=x"])
def test_remote_pages_need_no_key_or_cookie(
    remote_server: PageServer, path: str
) -> None:
    status, headers, body = request(remote_server, "GET", path)
    assert status in (200, 400, 404)
    assert "set-cookie" not in headers
    assert b"access key" not in body


def test_remote_page_is_served_and_static_stays_open(
    remote_server: PageServer,
) -> None:
    status, headers, body = request(remote_server, "GET", "/")
    assert status == 200
    assert "set-cookie" not in headers
    assert remote_server.token.encode() in body
    assert request(remote_server, "GET", "/static/app.js")[0] == 200


def test_key_query_is_ignored(remote_server: PageServer) -> None:
    status, headers, _ = request(remote_server, "GET", "/?k=anything")
    assert status == 200
    assert "set-cookie" not in headers


def test_remote_url_is_a_plain_ip_url(remote_server: PageServer) -> None:
    assert remote_server.url == f"http://127.0.0.1:{remote_server.port}/"


@pytest.mark.parametrize("bad", ["magic.tailnet.ts.net", "evil.example:80"])
def test_remote_refuses_other_hosts(remote_server: PageServer, bad: str) -> None:
    assert request(remote_server, "GET", "/", headers={"Host": bad})[0] == 403
    assert request(remote_server, "POST", "/comments", headers={"Host": bad})[0] == 403


def test_remote_post_refuses_bad_origin_and_missing_token(
    remote_server: PageServer,
) -> None:
    body = {"anchor": "x", "text": "t"}
    status, _, _ = request(
        remote_server,
        "POST",
        "/comments",
        headers={"Origin": "http://evil.example"},
        body=body,
    )
    assert status == 403
    assert request(remote_server, "POST", "/comments", token=False, body=body)[0] == 403


def test_edit_and_accept_are_403_without_allow_edit(remote_server: PageServer) -> None:
    for path in ("/edit", "/accept"):
        status, _, body = request(remote_server, "POST", path, body={})
        assert status == 403
        assert b"--allow-edit" in body
    status, _, _ = request(
        remote_server,
        "POST",
        "/comments",
        body={"anchor": "x", "text": "t"},
    )
    assert status == 201


def test_edit_passes_the_gate_with_allow_edit(editing_server: PageServer) -> None:
    status, _, body = request(editing_server, "POST", "/edit", body={})
    assert status == 400
    assert b"--allow-edit" not in body


def test_loopback_edit_stays_on(
    loopback_server: PageServer,
) -> None:
    assert request(loopback_server, "GET", "/")[0] == 200
    assert request(loopback_server, "POST", "/edit", body={})[0] == 400


def test_real_non_loopback_default_policy() -> None:
    from varde.pages import netbind

    assert netbind.is_loopback("127.0.0.1")
    assert not netbind.is_loopback("100.64.147.39")


def test_edit_denied_rule() -> None:
    assert edit_denied("/edit", True, False)
    assert edit_denied("/accept", True, False)
    assert not edit_denied("/edit", True, True)
    assert not edit_denied("/edit", False, False)
    assert not edit_denied("/comments", True, False)
