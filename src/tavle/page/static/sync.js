// Moving a block with insertBefore blurs whatever it holds; an untouched
// element the reader was typing in gets its focus back.
export function keepFocus(update) {
  const focused = document.activeElement;
  update();
  if (focused?.isConnected && document.activeElement !== focused) {
    focused.focus({ preventScroll: true });
  }
}

export function createSync(root, groupEnd, signature, initialThreadSignature) {
  let threadSignature = initialThreadSignature;
  // Bring the page's blocks in line with the fresh ones, touching a block only
  // when its hash changed so unchanged blocks and widget state stay.
  function syncBlocks(fresh) {
    const incoming = Array.from(fresh.querySelectorAll(':scope > .block'));
    const wanted = new Set(incoming.map((block) => block.dataset.anchor));
    const current = new Map();
    for (const block of root().querySelectorAll(':scope > .block')) {
      if (wanted.has(block.dataset.anchor)) current.set(block.dataset.anchor, block);
      else block.remove();
    }
    let cursor = root().querySelector(':scope > .block');
    for (const next of incoming) cursor = syncBlock(next, current, cursor);
  }

  function syncBlock(next, current, cursor) {
    const block = current.get(next.dataset.anchor);
    if (!block) {
      const added = document.importNode(next, true);
      added.classList.add('changed');
      if (cursor) root().insertBefore(added, cursor);
      else appendBlock(added);
      return cursor;
    }
    if (block !== cursor) root().insertBefore(block, cursor);
    else cursor = nextBlock(block);
    if (block.dataset.hash !== next.dataset.hash) {
      const replacement = document.importNode(next, true);
      replacement.classList.add('changed');
      block.replaceWith(replacement);
    }
    return cursor;
  }

  function appendBlock(added) {
    const blocks = root().querySelectorAll(':scope > .block');
    if (blocks.length) groupEnd(blocks[blocks.length - 1]).after(added);
    else root().prepend(added);
  }

  function nextBlock(block) {
    let node = block.nextElementSibling;
    while (node && !node.matches('.block')) node = node.nextElementSibling;
    return node;
  }

  function syncElement(fresh, selector) {
    const current = root().querySelector(selector);
    const incoming = fresh.querySelector(selector);
    if (current && !incoming) current.remove();
    else if (!current && incoming) root().prepend(document.importNode(incoming, true));
    else if (current && signature(current) !== signature(incoming)) {
      current.replaceWith(document.importNode(incoming, true));
    }
  }

  function syncOthers(fresh) {
    syncElement(fresh, ':scope > [data-vd-theme]');
    syncElement(fresh, ':scope > .doc-header');
    const incoming = Array.from(fresh.querySelectorAll(':scope > .thread, :scope > .orphans'));
    const joined = incoming.map((n) => signature(n)).join('');
    if (joined === threadSignature) return;
    threadSignature = joined;
    for (const old of root().querySelectorAll('.thread, .orphans')) old.remove();
    root().append(...incoming.map((node) => document.importNode(node, true)));
  }

  return { syncBlocks, syncOthers };
}
