// Tabs: panels with their labels as headings, each holding the blocks the server filled in.
// Props: panels (label, blocks). static/containers.js turns the panels into a tablist.
// The page's contents lists the tab names, so the block draws no "N tabs: ..." index line, and
// a contents link to a panel heading selects that tab (its heading is hidden while tabs show).
export function view(m, props, c, blockId, held) {
  const host = c.shared.containerView(m, 'tabs', props, blockId, held);
  host.attrs.oncreate = (vnode) => {
    const onClick = (event) => selectFromContents(vnode.dom, event);
    listeners.set(vnode.dom, onClick);
    document.addEventListener('click', onClick);
  };
  host.attrs.onremove = (vnode) => document.removeEventListener('click', listeners.get(vnode.dom));
  return host;
}

const listeners = new WeakMap();

function tabFor(host, hash) {
  const heading = hash && document.getElementById(decodeURIComponent(hash.slice(1)));
  const panel = heading && host.contains(heading) ? heading.closest('[role="tabpanel"]') : null;
  return panel && document.getElementById(panel.getAttribute('aria-labelledby'));
}

function selectFromContents(host, event) {
  const link = event.target.closest('.doc-toc a[href^="#"]');
  const tab = link && tabFor(host, link.hash);
  if (!tab) return;
  event.preventDefault();
  tab.click();
  tab.focus();
  host.scrollIntoView({ block: 'start' });
}

