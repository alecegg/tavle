// Per-block action menu: one button per block opens a popup of entries chosen by
// block type. The button shows on hover, on focus inside the block, or on a tap
// (the block gets .menu-active); at rest the page shows none. ES module loaded by app.js;
// `createMenu(root)` keeps one menu's state per mounted page (the document or a shadow root);
// createElement and textContent only. ENTRIES mirrors actions.menu_entries (allow_edit true; the
// server refuses an edit it does not allow); a Python test fails on drift.
import { overlayParent } from '../../static/dom.js';

export const ENTRIES = {"prose": ["comment", "suggest", "edit", "copy", "copy-link"], "heading": ["comment", "suggest", "edit", "copy", "copy-link"], "list": ["comment", "suggest", "edit", "copy", "copy-link"], "table": ["comment", "suggest", "edit", "copy", "copy-link"], "code": ["comment", "edit", "copy", "copy-link"], "widget": ["comment", "edit", "copy-link"], "decision": ["comment", "edit", "copy-link"], "visual": ["comment", "edit", "copy", "copy-link"], "status": ["comment", "edit", "copy-link"], "part": ["comment", "copy", "copy-link"], "error": ["comment", "edit", "copy", "copy-link"]};

const LABELS = { comment: 'Comment', suggest: 'Suggest', edit: 'Edit', copy: 'Copy', 'copy-link': 'Copy link' };
// Tap or click on a block's own text reveals its button; links and controls act as usual.
const OWN_CONTROLS = 'a, button, input, select, textarea, label, summary, [role="tab"], [contenteditable], .composer';

export function blockType(block) {
  if (block.dataset.blockType) return block.dataset.blockType;
  return block.dataset.part ? 'part' : 'prose';
}

export function entriesFor(block) {
  const ids = ENTRIES[blockType(block)] || ENTRIES.prose;
  return block.id ? ids : ids.filter((id) => id !== 'copy-link');
}

function copyText(block) {
  const marked = block.querySelector('[data-copy]');
  if (marked) return marked.dataset.copy;
  const clone = block.cloneNode(true);
  for (const node of clone.querySelectorAll('.menu-btn, .composer')) node.remove();
  return clone.textContent.replace(/\s+/g, ' ').trim();
}

function linkOf(block) {
  return location.origin + location.pathname + location.search + '#' + block.id;
}

function place(button, popup) {
  const anchor = button.getBoundingClientRect();
  const box = popup.getBoundingClientRect();
  const room = window.innerHeight - anchor.bottom;
  const top = room < box.height && anchor.top > room ? anchor.top - box.height : anchor.bottom;
  const left = Math.min(Math.max(anchor.right - box.width, 0), window.innerWidth - box.width);
  popup.style.insetBlockStart = Math.max(top, 0) + 'px';
  popup.style.insetInlineStart = Math.max(left, 0) + 'px';
}

// A rule or other decoration-only block has nothing to act on.
export function hasContent(block) {
  if (block.querySelector('[data-copy], .vb, input, select, textarea, img, svg')) return true;
  return block.textContent.trim() !== '';
}

// A tapped block's button appears just below the tap (above it near the bottom edge), inside the viewport,
// so a block taller than the screen never needs a scroll to reach its menu. Physical coordinates come from client rects.
function placeNearTap(block, event) {
  const button = block.querySelector(':scope > .menu-btn');
  if (!button) return;
  const size = button.offsetWidth;
  const margin = 8;
  const below = event.clientY + 12;
  const top = below + size > window.innerHeight - margin ? event.clientY - 12 - size : below;
  const rect = block.getBoundingClientRect();
  const left = Math.min(Math.max(event.clientX - size / 2, rect.left), rect.right - size);
  button.style.top = Math.max(top, margin) - rect.top + 'px';
  button.style.left = left - rect.left + 'px';
  button.style.bottom = 'auto';
  button.style.right = 'auto';
}

function clearPlacement(block) {
  const button = block.querySelector(':scope > .menu-btn');
  if (button) button.removeAttribute('style');
}

// The menu of one mounted page. `root` is the document or the shadow root the page lives in:
// lookups, the live region, popups and the copy buffer all stay inside it, and two menus share nothing.
export function createMenu(root) {
  const overlay = overlayParent(root);
  let current = null; // { button, popup }
  let active = null;
  let tapped = null; // { block, y }: where the last tap landed, from the block's top edge

  function announce(message) {
    let region = root.querySelector('.menu-live');
    if (!region) {
      region = document.createElement('div');
      region.className = 'menu-live';
      region.setAttribute('role', 'status');
      region.setAttribute('aria-live', 'polite');
      overlay.append(region);
    }
    region.textContent = message;
  }

  function fallbackCopy(text) {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('aria-hidden', 'true');
    area.className = 'menu-copy-buffer';
    overlay.append(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (error) { ok = false; }
    area.remove();
    return ok;
  }

  async function copy(text) {
    let ok = false;
    if (window.isSecureContext && navigator.clipboard) {
      try { await navigator.clipboard.writeText(text); ok = true; } catch (error) { ok = false; }
    }
    if (!ok) ok = fallbackCopy(text);
    announce(ok ? 'Copied' : 'Copy failed');
  }

  // An open popup closes on a press outside it, on resize, and on any scroll (it is fixed-position).
  // These listen only while it is open; the page's own scrollers and the host's both reach `closeOnScroll`.
  const dismissers = [
    [document, 'pointerdown', (event) => {
      const path = event.composedPath();
      if (!path.includes(current.popup) && !path.includes(current.button)) closeMenu(false);
    }, false],
    [window, 'resize', () => closeMenu(false), false],
    [window, 'scroll', () => closeMenu(false), true],
    [root, 'scroll', () => closeMenu(false), true],
  ];

  function closeMenu(restoreFocus) {
    if (!current) return;
    const { button, popup } = current;
    current = null;
    for (const [target, type, handler, capture] of dismissers) target.removeEventListener(type, handler, capture);
    popup.remove();
    button.setAttribute('aria-expanded', 'false');
    if (restoreFocus) button.focus();
  }

  function tapOffset(block) {
    return tapped && tapped.block === block ? tapped.y : null;
  }

  function runEntry(id, block, handlers) {
    if (id === 'comment') handlers.comment(block, undefined, tapOffset(block));
    else if (id === 'suggest' || id === 'edit') handlers.edit(block, id, tapOffset(block));
    else if (id === 'copy') copy(copyText(block));
    else if (id === 'copy-link') copy(linkOf(block));
  }

  function onKey(event, items) {
    const index = items.indexOf(root.activeElement);
    const last = items.length - 1;
    const moves = { ArrowDown: (index + 1) % items.length, ArrowUp: (index + last) % items.length, Home: 0, End: last };
    if (event.key === 'Escape') { event.preventDefault(); closeMenu(true); return; }
    if (event.key === 'Tab') { closeMenu(false); return; }
    if (!(event.key in moves)) return;
    event.preventDefault();
    items[moves[event.key]].focus();
  }

  function openMenu(block, button, handlers, focusLast) {
    closeMenu(false);
    const popup = document.createElement('div');
    popup.className = 'menu-popup';
    popup.setAttribute('role', 'menu');
    popup.setAttribute('aria-label', 'Actions');
    const shown = entriesFor(block).filter((id) => !(handlers.readOnly && (id === 'suggest' || id === 'edit')));
    const items = shown.map((id) => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'menu-item';
      item.setAttribute('role', 'menuitem');
      item.tabIndex = -1;
      item.dataset.entry = id;
      item.textContent = LABELS[id];
      item.addEventListener('click', () => {
        closeMenu(id === 'comment' || id === 'copy' || id === 'copy-link');
        runEntry(id, block, handlers);
      });
      return item;
    });
    popup.append(...items);
    popup.addEventListener('keydown', (event) => onKey(event, items));
    overlay.append(popup);
    place(button, popup);
    button.setAttribute('aria-expanded', 'true');
    current = { button, popup };
    for (const [target, type, handler, capture] of dismissers) target.addEventListener(type, handler, capture);
    items[focusLast ? items.length - 1 : 0].focus();
  }

  function mountMenu(block, handlers) {
    if (block.querySelector(':scope > .menu-btn') || !hasContent(block)) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'menu-btn';
    button.textContent = '⋯';
    const label = block.textContent.replace(/\s+/g, ' ').trim().slice(0, 40);
    button.setAttribute('aria-label', 'Actions for ' + (label || 'block'));
    button.setAttribute('aria-haspopup', 'menu');
    button.setAttribute('aria-expanded', 'false');
    button.addEventListener('click', () => {
      if (current && current.button === button) closeMenu(true);
      else openMenu(block, button, handlers, false);
    });
    button.addEventListener('keydown', (event) => {
      if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
      event.preventDefault();
      openMenu(block, button, handlers, event.key === 'ArrowUp');
    });
    block.classList.add('has-menu');
    block.append(button);
  }

  function setActive(block, event) {
    if (active && active !== block) {
      active.classList.remove('menu-active');
      clearPlacement(active);
    }
    active = block;
    tapped = null;
    if (!active) return;
    active.classList.add('menu-active');
    if (!event) return;
    placeNearTap(active, event);
    tapped = { block: active, y: event.clientY - active.getBoundingClientRect().top };
  }

  function onTap(event) {
    if (event.pointerType === 'mouse') return; // a mouse reveals by hover
    if (!(event.target instanceof Element) || event.target.closest('.menu-popup, .menu-btn')) return;
    if (event.target.closest(OWN_CONTROLS)) return;
    setActive(event.target.closest('.block.has-menu'), event);
  }

  root.addEventListener('click', onTap);

  function destroy() {
    closeMenu(false);
    root.removeEventListener('click', onTap);
  }

  return { mountMenu, destroy };
}
