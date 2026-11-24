// Entry for mounting a page into a root: `mountPage(root, { apiBase, pageUrl, token, refresh, readOnly })`.
// `root` is the document or the shadow root of a host page (the dashboard). The served page
// mounts itself from its script tags (`mountDocument`, options from the body data attributes and
// the token meta); calling this for the same root again returns the mount it already has.
//
// Options: `apiBase` posts to `{apiBase}/comments{apiQuery}` with no token and no live editing; `pageUrl` is
// where a refresh reads the page; `token` is sent when `apiBase` is empty; `refresh` is an optional
// `() => Promise<string>` returning the page's fresh HTML instead of fetching `pageUrl`; `readOnly`
// shows no block menu (the host disables the page's own controls).
//
// A shadow-root mount opens no EventSource and no parent message listener: the host calls the
// returned `refresh()`. `destroy()` removes everything the mount registered. `varde` is the
// mount's own helper object (what `window.varde` is for the document page).
// Styling: the page stylesheet (`static/app.css`) puts its tokens, `body` look and `scroll-padding`
// on `:host` as well as `:root`, so loading it into the shadow root styles the page. The host
// page decides the scroller: make `:host` (or an ancestor) the scroll container, or let the window
// scroll; contents-nav jumps use `scrollIntoView` and so reach whichever scrolls. Popups, dialogs and
// the copy buffer are appended inside the shadow root. The component bundle (`components.js`) boots
// on the document only; the host mounts client-side blocks in its root itself.
const PARTS = ['./app.js', './blocks.js', './inputs_fields.js', './inputs_widgets.js', './inputs_runtime.js', './recap.js', './inputs_ordered.js'];

export async function mountPage(root, { apiBase = '', apiQuery = '', pageUrl = '/', token = '', refresh, readOnly = false } = {}) {
  await Promise.all(PARTS.map((part) => import(part)));
  return globalThis.vardePageParts.mount(root, { apiBase, apiQuery, pageUrl, token, refresh, readOnly });
}
