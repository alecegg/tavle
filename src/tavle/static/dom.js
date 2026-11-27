// DOM builders shared by the block modules: createElement and textContent only.
export const SVG_NS = 'http://www.w3.org/2000/svg';

export function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Where a page's popups, dialogs and scratch nodes go: inside the shadow root the page is
// mounted in, else the document body. Never the host document for an inline page.
export function overlayParent(node) {
  const tree = node.getRootNode();
  return tree instanceof ShadowRoot ? tree : document.body;
}

// The element focused in the tree `node` lives in (a shadow root keeps its own), or null
// when none is: a document reports document.body as its active element then.
export function focusedIn(node) {
  const active = node.getRootNode().activeElement;
  return active && active !== document.body ? active : null;
}

// A window event that acts for `node` only: it stops, and unhooks itself, once `node` leaves the page.
export function whileConnected(node, type, handler) {
  const run = (event) => {
    if (!node.isConnected) return window.removeEventListener(type, run);
    handler(event);
  };
  window.addEventListener(type, run);
}

export function control(label, onClick, className, aria) {
  const node = make('button', className || 'vb-ctl', label);
  node.type = 'button';
  if (aria) node.setAttribute('aria-label', aria);
  node.addEventListener('click', onClick);
  return node;
}

export function svgNode(tag, attrs, className) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attrs || {})) node.setAttribute(name, value);
  if (className) node.setAttribute('class', className);
  return node;
}

// Scroll `view` so a focused `target` and its focus ring sit inside its scrollport.
// Browsers treat sticky elements as already in view, so tables call this themselves.
// insetTop reserves a sticky header; vertical: false leaves scrollTop alone.
export function keepInside(view, target, { margin = 4, insetTop = 0, vertical = true } = {}) {
  const box = view.getBoundingClientRect();
  const rect = target.getBoundingClientRect();
  const left = box.left + view.clientLeft + margin;
  const right = box.left + view.clientLeft + view.clientWidth - margin;
  const top = box.top + view.clientTop + margin + insetTop;
  const bottom = box.top + view.clientTop + view.clientHeight - margin;
  if (rect.width <= right - left) {
    if (rect.left < left) view.scrollLeft -= left - rect.left;
    else if (rect.right > right) view.scrollLeft += rect.right - right;
  }
  if (!vertical || rect.height > bottom - top) return;
  if (rect.top < top) view.scrollTop -= top - rect.top;
  else if (rect.bottom > bottom) view.scrollTop += rect.bottom - bottom;
}
