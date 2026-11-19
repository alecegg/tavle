// Mount contract. A block host is `<div data-mithril="NAME">` holding one
// `<script type="application/json">` with the props and a `<noscript>` fallback.
// The host's `data-block-id` (when the block has an id) is the view's fourth argument.
// Inside a `[data-readonly]` page (a static export) every control is disabled.
// A container host also holds its held blocks as `[data-hold]` children; they are lifted out and
// passed as `held` (id -> element) because rendering replaces the host's children.
// Mounting replaces the host's children with the component's DOM, then fires a bubbling
// `vd-mounted` event so enhancers (blocks.js) can wire the new block.
export function mountComponents(root, m, components) {
  let mounted = 0;
  for (const host of root.querySelectorAll('[data-mithril]:not([data-mounted])')) {
    const component = components[host.dataset.mithril];
    const holder = host.querySelector('script[type="application/json"]');
    if (!component || !component.view || !holder) continue;
    host.dataset.mounted = '1';
    const held = new Map([...host.querySelectorAll(':scope > [data-hold]')].map((slot) => [slot.dataset.hold, slot]));
    held.forEach((slot) => slot.remove());
    m.render(host, component.view(m, JSON.parse(holder.textContent), components, host.dataset.blockId, held));
    if (host.closest('[data-readonly]')) {
      for (const control of host.querySelectorAll('button, input, select, textarea')) control.disabled = true;
    }
    host.dispatchEvent(new CustomEvent('vd-mounted', { bubbles: true }));
    mounted += 1;
  }
  return mounted;
}
