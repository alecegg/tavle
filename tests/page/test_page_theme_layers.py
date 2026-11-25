from pathlib import Path

from tavle import doc_theme, no_layers, parse_toml


def test_caller_layers_and_front_matter(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    layer = parse_toml('preset = "harbor"', "caller")

    def layers(_doc: Path):
        return [(layer, "caller")]

    themed = doc_theme(doc, "# Page", layers)
    default = doc_theme(doc, "# Page", no_layers)
    overridden = doc_theme(doc, "---\ntheme: varde\n---\n# Page", layers)
    assert themed.tokens != default.tokens
    assert overridden.tokens == default.tokens


def test_theme_file_edit_visible_on_next_request(tmp_path: Path) -> None:
    import http.client
    import threading

    from tavle import PageServer

    doc = tmp_path / "page.md"
    doc.write_text("# Page", encoding="utf-8")
    theme_file = tmp_path / "theme.toml"
    theme_file.write_text('preset = "harbor"', encoding="utf-8")

    def layers(_doc: Path):
        return [
            (parse_toml(theme_file.read_text(encoding="utf-8"), "caller"), "caller")
        ]

    server = PageServer(doc, theme_layers=layers)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:

        def get(path: str) -> bytes:
            conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
            try:
                conn.request("GET", path)
                response = conn.getresponse()
                assert response.status == 200
                return response.read()
            finally:
                conn.close()

        assert b"/theme.css?v=" in get("/")
        first = get("/theme.css")
        theme_file.write_text('preset = "varde"', encoding="utf-8")
        assert get("/theme.css") != first
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
