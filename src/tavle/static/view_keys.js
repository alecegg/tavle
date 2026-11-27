// Keyboard and pointer state shared by the selectable views (diagram, flow, wireframe, screen flow).
const ACTIVATE = new Set(['Enter', ' ']);
const STEP = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
export const ARROWS = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp'];
export const ARROWS_AND_ENDS = [...ARROWS, 'Home', 'End'];

// The item an arrow, Home or End `key` moves to from `item` in `list`, wrapping at both ends.
export function itemAfter(list, item, key) {
  const at = list.indexOf(item);
  let next = at + (STEP[key] || 0);
  if (key === 'Home') next = 0;
  if (key === 'End') next = list.length - 1;
  return list[(next + list.length) % list.length];
}

// Call `onItem(element)` when focus enters an item matching `selector` inside `view`.
export function onItemFocus(view, selector, onItem) {
  view.addEventListener('focusin', (event) => {
    const target = event.target.closest(selector);
    if (target) onItem(target);
  });
}

// Hover and focus of a selectable view. `keyOf(element)` names the item an element stands for
// (null for none); the key is kept in state.hover or state.focus, and `paint` redraws after each change.
export function bindHoverAndFocus(view, { selector, state, keyOf, paint }) {
  view.addEventListener('focusout', () => { state.focus = null; paint(); });
  view.addEventListener('pointerover', (event) => {
    state.hover = keyOf(event.target.closest(selector));
    paint();
  });
  view.addEventListener('pointerleave', () => { state.hover = null; paint(); });
}

function actionFor(key, actions) {
  if (key === 'Escape') return actions.clear;
  if (ACTIVATE.has(key)) return actions.activate;
  return actions.moveKeys.includes(key) ? actions.move : null;
}

// Run the action bound to the event's key; `move` receives the key. Other keys stay with the browser.
export function handleViewKey(event, actions) {
  const action = actionFor(event.key, actions);
  if (!action) return;
  event.preventDefault();
  action(event.key);
}
