// Columns: a grid of panels, each holding the blocks the server filled in. Props: panels (label, blocks).
export function view(m, props, c, blockId, held) {
  return c.shared.containerView(m, 'columns', props, blockId, held);
}
