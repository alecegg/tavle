"""Chromium checks that `mountPage` runs a page inside a shadow root (slow tier).

The harness page has no page scripts of its own: it copies the served page's
`<main>` into a shadow root next to an outside element and mounts it there, as
the dashboard does.
"""

# ruff: noqa: E501  (inline JS probes)

from __future__ import annotations

import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tavle import PageServer

pytestmark = pytest.mark.slow

DOC = (
    "# Plan\n\nAlpha paragraph.\n\n## Part one\n\n## Part two\n\n## Part three\n\n"
    + "Filler line.\n\n" * 60
    + "## Part four\n\nOmega paragraph.\n"
)
HARNESS = (
    "<!doctype html><body><div id='outside' style='height:40px'>outside</div>"
    "<div id='host-a'></div><div id='host-b'></div></body>"
)
EXTRA = (
    '<div class="block vb vd-image" data-anchor="img"><a class="vd-image-link" href="/x.png">'
    '<img alt="A" src="data:image/gif;base64,R0lGODlhAQABAAAAACw="></a></div>'
    '<div class="block vb vd-code" data-anchor="code" data-copy="x = 1">'
    '<div class="vd-code-head"></div></div>'
    '<div class="block vb" data-anchor="chart"><div class="chart"><div class="vb-plot">'
    '<svg class="vb-chart" aria-label="C"></svg></div><details class="vb-data">'
    "<summary>Data</summary></details></div></div>"
)
MOUNT = """async ([hostId, extra, options]) => {
  const [html, css] = await Promise.all([
    fetch('/').then((r) => r.text()), fetch('/static/app.css').then((r) => r.text())]);
  const parsed = new DOMParser().parseFromString(html, 'text/html');
  const main = document.importNode(parsed.querySelector('main[data-role="page"]'), true);
  if (extra) main.insertAdjacentHTML('beforeend', extra);
  const token = parsed.querySelector('meta[name="tavle-token"]').content;
  const style = document.createElement('style');
  style.textContent = css;
  const shadow = document.getElementById(hostId).attachShadow({ mode: 'open' });
  shadow.append(style, main);
  const { mountPage } = await import('/static/page.js');
  window.mounts = window.mounts || {};
  const { customRefresh, ...rest } = options;
  const refresh = customRefresh && (async () => { window.customCalls = (window.customCalls || 0) + 1; return html; });
  window.mounts[hostId] = await mountPage(shadow, { pageUrl: '/', token, refresh, ...rest });
}"""
IN_SHADOW = "(id) => document.getElementById(id).shadowRoot"


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page(viewport={"width": 900, "height": 600})
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def site(tmp_path: Path, shared_page: Any) -> Iterator[tuple[Any, PageServer]]:
    doc = tmp_path / "plan.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.port}"
    shared_page.route(
        f"{base}/harness", lambda r: r.fulfill(body=HARNESS, content_type="text/html")
    )
    shared_page.goto(f"{base}/harness")
    yield shared_page, server
    shared_page.unroute(f"{base}/harness")
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def mount(page: Any, host_id: str = "host-a", extra: str = "", **options: Any) -> None:
    page.evaluate(MOUNT, [host_id, extra, options])
    page.wait_for_function(
        "(id) => document.getElementById(id).shadowRoot.querySelector('.menu-btn')",
        arg=host_id,
    )


def count_in(page: Any, selector: str, where: str = "shadow") -> int:
    script = (
        "([s]) => document.getElementById('host-a').shadowRoot.querySelectorAll(s).length"
        if where == "shadow"
        else "([s]) => document.body.querySelectorAll(s).length"
    )
    return page.evaluate(script, [selector])


def open_menu(page: Any) -> None:
    block = page.locator("#host-a .block", has_text="Alpha").first
    block.hover()
    block.locator(".menu-btn").click()


def test_menu_popup_live_region_and_composer_stay_in_the_root(
    site: tuple[Any, PageServer],
) -> None:
    page, _ = site
    mount(page)
    open_menu(page)
    assert count_in(page, ".menu-popup") == 1
    assert count_in(page, ".menu-popup", "document") == 0
    page.locator('#host-a .menu-item[data-entry="copy-link"]').click()
    page.wait_for_function(
        "() => document.getElementById('host-a').shadowRoot.querySelector('.menu-live')?.textContent"
    )
    assert count_in(page, ".menu-live", "document") == 0
    open_menu(page)
    page.locator('#host-a .menu-item[data-entry="comment"]').click()
    assert count_in(page, ".composer textarea") == 1
    assert (
        page.evaluate(
            "() => document.getElementById('host-a').shadowRoot.activeElement?.tagName"
        )
        == "TEXTAREA"
    )
    assert page.evaluate("() => document.activeElement.id") == "host-a"


def test_comment_posts_with_the_mount_token(site: tuple[Any, PageServer]) -> None:
    page, _ = site
    mount(page)
    open_menu(page)
    page.locator('#host-a .menu-item[data-entry="comment"]').click()
    page.locator("#host-a .composer textarea").fill("hello")
    with page.expect_request(
        lambda r: r.method == "POST" and r.url.endswith("/comments")
    ) as sent:
        page.locator("#host-a .composer .primary").click()
    assert sent.value.headers["x-tavle-token"]
    assert '"text":"hello"' in sent.value.post_data


def test_press_outside_the_shadow_closes_the_menu(site: tuple[Any, PageServer]) -> None:
    page, _ = site
    mount(page)
    open_menu(page)
    assert count_in(page, ".menu-popup") == 1
    page.locator("#outside").click()
    assert count_in(page, ".menu-popup") == 0
    open_menu(page)
    page.keyboard.press("Escape")
    assert count_in(page, ".menu-popup") == 0


def test_each_mount_has_its_own_helpers_and_window_tavle_is_unset(
    site: tuple[Any, PageServer],
) -> None:
    page, _ = site
    mount(page, "host-a")
    mount(page, "host-b")
    same = page.evaluate(
        """() => {
          const [a, b] = [window.mounts['host-a'].tavle, window.mounts['host-b'].tavle];
          a.formState.set('x', 1);
          a.register('probe', { hydrate() {} });
          return [a === b, b.formState.get('x'), window.tavle === undefined, Boolean(a.inputs)];
        }"""
    )
    assert same == [False, None, True, True]


def test_inline_mount_opens_no_event_stream_and_ignores_the_parent_message(
    site: tuple[Any, PageServer],
) -> None:
    page, _ = site
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url))
    mount(page)
    page.evaluate(
        "() => window.postMessage({ type: 'tavle-refresh' }, location.origin)"
    )
    page.wait_for_timeout(500)
    assert not [u for u in seen if u.endswith("/events")]
    before = len([u for u in seen if u.endswith("/") and "/harness" not in u])
    page.evaluate("() => window.mounts['host-a'].refresh()")
    after = len([u for u in seen if u.endswith("/") and "/harness" not in u])
    assert after == before + 1


def test_refresh_option_supplies_the_fresh_page(site: tuple[Any, PageServer]) -> None:
    page, _ = site
    seen: list[str] = []
    mount(page, customRefresh=True)
    page.on("request", lambda r: seen.append(r.url))
    page.evaluate("() => window.mounts['host-a'].refresh()")
    assert page.evaluate("() => window.customCalls") == 1
    assert not [u for u in seen if u.endswith("/") and "/harness" not in u]


def test_toc_link_scrolls_in_the_root_without_touching_the_url(
    site: tuple[Any, PageServer],
) -> None:
    page, _ = site
    mount(page)
    before = page.evaluate("() => location.href")
    assert page.evaluate("() => window.scrollY") == 0
    page.locator('#host-a nav.doc-toc a[href^="#h-"]').last.evaluate("(a) => a.click()")
    top = page.evaluate(
        """() => {
          const root = document.getElementById('host-a').shadowRoot;
          const id = root.querySelector('nav.doc-toc li:last-child a').getAttribute('href').slice(1);
          return [window.scrollY, root.getElementById(id).getBoundingClientRect().top];
        }"""
    )
    assert top[0] > 0 and 0 <= top[1] < 600
    assert page.evaluate("() => location.href") == before


def test_code_copy_buffer_and_image_dialog_stay_in_the_root(
    site: tuple[Any, PageServer],
) -> None:
    page, _ = site
    mount(page, extra=EXTRA)
    page.evaluate(
        """() => {
          Object.defineProperty(navigator, 'clipboard', { value: undefined });
          window.added = [];
          const watch = (node, name) => new MutationObserver((list) => {
            for (const r of list) for (const n of r.addedNodes) window.added.push([name, n.className || n.tagName]);
          }).observe(node, { childList: true });
          watch(document.body, 'body');
          watch(document.getElementById('host-a').shadowRoot, 'shadow');
        }"""
    )
    page.locator("#host-a .vd-code-copy").click()
    page.locator("#host-a a.vd-image-link").click()
    added = page.evaluate("() => window.added")
    assert ["shadow", "vd-code-scratch"] in added
    assert ["shadow", "vd-image-dialog"] in added
    assert not [a for a in added if a[0] == "body"]
    assert page.evaluate(
        "() => document.getElementById('host-a').shadowRoot.querySelector('dialog.vd-image-dialog').open"
    )


def test_print_hooks_open_only_the_mounted_charts(site: tuple[Any, PageServer]) -> None:
    page, _ = site
    page.evaluate(
        """() => {
          const outside = document.createElement('div');
          outside.className = 'chart';
          outside.innerHTML = '<details class="vb-data"></details>';
          outside.id = 'outside-chart';
          document.body.append(outside);
        }"""
    )
    mount(page, extra=EXTRA)
    page.wait_for_function(  # chart hooks load after the mount resolves
        "() => document.getElementById('host-a').shadowRoot.querySelector('.vb-readout')"
    )
    states = page.evaluate(
        """() => {
          const inside = () => document.getElementById('host-a').shadowRoot.querySelector('details.vb-data').open;
          const outer = () => document.querySelector('#outside-chart details').open;
          window.dispatchEvent(new Event('beforeprint'));
          const during = [inside(), outer()];
          window.dispatchEvent(new Event('afterprint'));
          return [during, [inside(), outer()]];
        }"""
    )
    assert states == [[True, False], [False, False]]


def test_page_css_tokens_apply_under_host(site: tuple[Any, PageServer]) -> None:
    page, _ = site
    mount(page)
    value = page.evaluate(
        """() => {
          const main = document.getElementById('host-a').shadowRoot.querySelector('main');
          return getComputedStyle(main).getPropertyValue('--vd-space-9').trim();
        }"""
    )
    assert value


def test_mounting_one_root_twice_returns_the_same_mount(
    site: tuple[Any, PageServer],
) -> None:
    page, _ = site
    mount(page)
    same = page.evaluate(
        """async () => {
          const { mountPage } = await import('/static/page.js');
          const root = document.getElementById('host-a').shadowRoot;
          return (await mountPage(root, { pageUrl: '/' })) === window.mounts['host-a'];
        }"""
    )
    assert same is True
    assert count_in(page, ".menu-btn") == count_in(page, ".block:not(:has(hr))")
