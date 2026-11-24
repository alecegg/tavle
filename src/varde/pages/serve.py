"""Loopback HTTP server for one markdown doc: page, comments, live updates."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, unquote, urlsplit

from varde.pages.assemble import (
    assemble_page,
)
from varde.pages.comments import (
    comments_path,
    fold,
    mark_applied,
    read_rows,
)
from varde.pages.edit import (
    EditError,
    accept_replacement,
    apply_edit,
    read_block,
)
from varde.pages.netbind import (
    LOOPBACK,
    allowed_hosts,
    allowed_origins,
    classify_host,
    is_loopback,
)
from varde.pages.server_parts import (
    MAX_BODY,
    MAX_STREAMS,
    READ_TIMEOUT,
    SECURITY_HEADERS,
    TOKEN_HEADER,
    Broadcaster,
    host_allowed,
    is_json_type,
    new_token,
    origin_allowed,
    token_matches,
    watch_files,
    write_event_stream,
)
from varde.pages.store import EDIT_OFF, sources_for, store_comment
from varde.pages.template import BUNDLE_SCRIPT, page_css, static_file, static_scripts
from varde.pages.theme.page import doc_theme
from varde.pages.validation import parse_json_object, strings
from varde.ui.components import component_bundle
from varde.ui.media import Problem, load
from varde.ui.shell import TOKENS_CSS
from varde.ui.theme.css import theme_css
from varde.ui.theme.tokens import ThemeError

# `app.css` without the tokens: the host page that mounts a page owns them
INLINE_CSS = "app-inline.css"


def static_body(name: str) -> bytes:
    if name == "app.css":
        return page_css().encode("utf-8")
    if name == INLINE_CSS:
        return page_css(skip=(TOKENS_CSS,)).encode("utf-8")
    if name == BUNDLE_SCRIPT:
        return component_bundle().encode("utf-8")
    return static_file(name).read_bytes()


STATIC_TYPES = {
    **dict.fromkeys(static_scripts(), "text/javascript; charset=utf-8"),
    BUNDLE_SCRIPT: "text/javascript; charset=utf-8",
    "app.css": "text/css; charset=utf-8",
    INLINE_CSS: "text/css; charset=utf-8",
}
ACTOR = "user"  # the page user; recorded as the actor that applied a suggestion


def parse_edit_body(raw: bytes) -> tuple[str, str, str]:
    """Return (anchor, base_hash, new_source) or raise ValueError."""
    data = parse_json_object(raw)
    anchor, base_hash, new_source = strings(data, "anchor", "base_hash", "new_source")
    return anchor, base_hash, new_source


def parse_accept_body(raw: bytes) -> tuple[str, str]:
    """Return (comment_id, base_hash) or raise ValueError."""
    comment_id, base_hash = strings(parse_json_object(raw), "comment_id", "base_hash")
    return comment_id, base_hash


def render_document(doc: Path, token: str, api_base: str = "") -> str:
    return assemble_page(doc, token=token, api_base=api_base)


class PageServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    # The socketserver default of 5 overflows when a page loads its widget modules
    # at once; the kernel then resets the extra connections.
    request_queue_size = 128

    def __init__(
        self,
        doc: Path,
        port: int = 0,
        host: str = LOOPBACK,
        allow_edit: bool = False,
    ) -> None:
        self.doc = doc
        self.host = classify_host(host)
        self.remote = not is_loopback(self.host)  # tests may override
        self.allow_edit = allow_edit
        self.token = new_token()
        self.broadcaster = Broadcaster()
        self._poller: threading.Thread | None = None
        self._halt = threading.Event()
        self.streams = 0
        self.streams_lock = threading.Lock()
        self.edit_lock = threading.Lock()
        # Test hook: called with (method, path, Host) for every request.
        self.recorder: Callable[[str, str, str], None] | None = None
        super().__init__((self.host, port), PageHandler)
        self.port = self.server_address[1]
        self.hosts = allowed_hosts(self.host, self.port)
        self.origins = allowed_origins(self.host, self.port)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        self._poller = threading.Thread(
            target=watch_files,
            args=(
                (self.doc, comments_path(self.doc)),
                self.broadcaster,
                self._halt,
            ),
            daemon=True,
        )
        self._poller.start()
        try:
            super().serve_forever(poll_interval)
        finally:
            self._halt.set()
            self.broadcaster.stop()

    def shutdown(self) -> None:
        self._halt.set()
        self.broadcaster.stop()
        super().shutdown()


EDIT_ROUTES = frozenset({"/edit", "/accept"})


def edit_denied(path: str, remote: bool, allow_edit: bool) -> bool:
    return remote and not allow_edit and path in EDIT_ROUTES


class PageHandler(BaseHTTPRequestHandler):
    timeout = READ_TIMEOUT  # socket timeout: stalled clients free their thread
    header_override: dict[str, str] | None = None

    @property
    def app(self) -> PageServer:
        return cast("PageServer", self.server)

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def end_headers(self) -> None:
        for name, value in (self.header_override or SECURITY_HEADERS).items():
            self.send_header(name, value)
        self.header_override = None
        super().end_headers()

    def _record(self) -> None:
        if self.app.recorder is not None:
            host = self.headers.get("Host") or ""
            self.app.recorder(self.command, self.path, host)

    def _reply(
        self,
        status: int,
        body: bytes,
        content_type: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Send a reply; `headers` replaces the parent page's security headers."""
        self.header_override = headers
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _reject(self, status: HTTPStatus, reason: str) -> None:
        self.close_connection = True
        self._reply(status, reason.encode(), "text/plain; charset=utf-8")

    def _host_ok(self) -> bool:
        if host_allowed(self.headers.get("Host"), self.app.hosts):
            return True
        self._reject(HTTPStatus.FORBIDDEN, "bad host")
        return False

    def do_GET(self) -> None:
        self._record()
        if not self._host_ok():
            return
        path = urlsplit(self.path).path
        if path == "/events":
            self._stream_events()
            return
        try:
            self._get_content(path)
        except Exception:  # noqa: BLE001
            self._reject(HTTPStatus.INTERNAL_SERVER_ERROR, "internal error")

    def _get_content(self, path: str) -> None:
        if path == "/":
            self._send_page()
            return
        name = path.removeprefix("/static/") if path.startswith("/static/") else None
        if name in STATIC_TYPES:
            body = static_body(name)
            self._reply(HTTPStatus.OK, body, STATIC_TYPES[name])
            return
        if path == "/theme.css":
            self._send_theme()
            return
        if path == "/block":
            self._send_block(urlsplit(self.path).query)
            return
        if path.startswith("/media/"):
            self._send_media(unquote(path.removeprefix("/media/")))
            return
        self._reject(HTTPStatus.NOT_FOUND, "not found")

    def _send_theme(self) -> None:
        """The page's theme CSS; no theme or an invalid one is a 404."""
        try:
            theme = doc_theme(self.app.doc, self.app.doc.read_text(encoding="utf-8"))
        except ThemeError:
            theme = None
        if theme is None or not theme.active:
            self._reject(HTTPStatus.NOT_FOUND, "not found")
            return
        self._reply(HTTPStatus.OK, theme_css(theme).encode(), "text/css; charset=utf-8")

    def _send_media(self, src: str) -> None:
        """An image file under the page's directory; anything else is a 404."""
        found = load(src, self.app.doc.parent)
        if isinstance(found, Problem):
            self._reject(HTTPStatus.NOT_FOUND, "not found")
            return
        self._reply(HTTPStatus.OK, found[0], found[1])

    def _send_page(self) -> None:
        page = render_document(self.app.doc, self.app.token)
        self._reply(HTTPStatus.OK, page.encode(), "text/html; charset=utf-8")

    def _stream_events(self) -> None:
        if self.headers.get("Sec-Fetch-Site", "same-origin") not in {
            "same-origin",
            "none",
        }:
            self._reject(HTTPStatus.FORBIDDEN, "cross-site")
            return
        with self.app.streams_lock:
            if self.app.streams >= MAX_STREAMS:
                self._reject(HTTPStatus.SERVICE_UNAVAILABLE, "too many streams")
                return
            self.app.streams += 1
        try:
            self._send_stream()
        finally:
            with self.app.streams_lock:
                self.app.streams -= 1

    def _send_stream(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        write_event_stream(self.wfile, self.app.broadcaster)

    def do_POST(self) -> None:
        self._record()
        if not self._host_ok():
            return
        path = urlsplit(self.path).path
        handler = self._post_routes().get(path)
        if handler is None:
            self._reject(HTTPStatus.NOT_FOUND, "not found")
            return
        if not origin_allowed(self.headers.get("Origin"), self.app.origins):
            self._reject(HTTPStatus.FORBIDDEN, "bad origin")
            return
        if not is_json_type(self.headers.get("Content-Type")):
            self._reject(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "json required")
            return
        if not token_matches(self.headers.get(TOKEN_HEADER), self.app.token):
            self._reject(HTTPStatus.FORBIDDEN, "bad token")
            return
        if edit_denied(path, self.app.remote, self.app.allow_edit):
            self._reject(HTTPStatus.FORBIDDEN, EDIT_OFF)
            return
        raw = self._read_body()
        if raw is not None:
            handler(raw)

    def _post_routes(self) -> dict[str, Callable[[bytes], None]]:
        return {
            "/comments": self._store_comment,
            "/edit": self._store_edit,
            "/accept": self._accept_suggestion,
        }

    def _read_body(self) -> bytes | None:
        length = self.headers.get("Content-Length", "")
        if not length.isascii() or not length.isdigit():
            self._reject(HTTPStatus.LENGTH_REQUIRED, "content-length required")
            return None
        if int(length) > MAX_BODY:
            # Drain a modest body so the client reads the 413, not a reset.
            self.rfile.read(min(int(length), 4 * MAX_BODY))
            self._reject(HTTPStatus.CONTENT_TOO_LARGE, "body too large")
            return None
        return self.rfile.read(int(length))

    def _store_comment(self, raw: bytes) -> None:
        # An answer is a comment row, open on any bind (user, 2026-11-19).
        try:
            sources = sources_for(self.app.doc, raw)
            row = store_comment(self.app.doc, raw, sources=sources)
        except ValueError as error:
            self._reject(HTTPStatus.BAD_REQUEST, str(error))
            return
        body = json.dumps({"id": row["id"]}).encode()
        self._reply(HTTPStatus.CREATED, body, "application/json")

    def _store_edit(self, raw: bytes) -> None:
        try:
            anchor, base_hash, new_source = parse_edit_body(raw)
            apply_edit(self.app.doc, self.app.edit_lock, anchor, base_hash, new_source)
        except ValueError as error:
            self._reject(HTTPStatus.BAD_REQUEST, str(error))
            return
        except EditError as error:
            self._reject(HTTPStatus(error.status), str(error))
            return
        self.app.broadcaster.publish()
        self._reply(HTTPStatus.OK, b"{}", "application/json")

    def _accept_suggestion(self, raw: bytes) -> None:
        try:
            comment_id, base_hash = parse_accept_body(raw)
            found = [c for c in fold(read_rows(self.app.doc)) if c["id"] == comment_id]
            suggestion = found[0] if found else None
            if suggestion is None or suggestion.get("kind") != "suggestion":
                self._reject(HTTPStatus.NOT_FOUND, "unknown suggestion")
                return
            if suggestion.get("state") != "open":
                self._reject(HTTPStatus.CONFLICT, "suggestion already closed")
                return
            accept_replacement(
                self.app.doc,
                self.app.edit_lock,
                suggestion["anchor"],
                base_hash,
                (suggestion.get("quote", ""), suggestion.get("replacement", "")),
                lambda: mark_applied(self.app.doc, comment_id, ACTOR),
            )
        except ValueError as error:
            self._reject(HTTPStatus.BAD_REQUEST, str(error))
            return
        except EditError as error:
            self._reject(HTTPStatus(error.status), str(error))
            return
        self.app.broadcaster.publish()
        self._reply(HTTPStatus.OK, b"{}", "application/json")

    def _send_block(self, query: str) -> None:
        anchor = (parse_qs(query).get("anchor") or [""])[0]
        try:
            found = read_block(self.app.doc, anchor)
        except EditError as error:
            self._reject(HTTPStatus(error.status), str(error))
            return
        body = json.dumps({"hash": found.block.hash, "source": found.source}).encode()
        self._reply(HTTPStatus.OK, body, "application/json")

    def _method_not_allowed(self) -> None:
        self._record()
        if self._host_ok():
            self._reject(HTTPStatus.METHOD_NOT_ALLOWED, "method not allowed")

    do_HEAD = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _method_not_allowed


def serve(
    doc: Path,
    port: int = 0,
    on_ready: Any = None,
    host: str = LOOPBACK,
    allow_edit: bool = False,
) -> None:
    """Serve `doc` in the foreground until interrupted."""
    server = PageServer(doc, port, host, allow_edit)
    try:
        if on_ready is not None:
            on_ready(server.url)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
