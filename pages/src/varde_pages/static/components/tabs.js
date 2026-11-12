// Tabs: panels with their labels as headings, each holding the blocks the server filled in.
// Props: panels (label, blocks). static/containers.js turns the panels into a tablist.
export function view(m, props, c, blockId, held) {
  return c.shared.containerView(m, 'tabs', props, blockId, held);
}
