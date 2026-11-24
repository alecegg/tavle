// Keyboard dispatch shared by the selectable views (diagram, wireframe, screen flow).
const ACTIVATE = new Set(['Enter', ' ']);
export const ARROWS = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp'];
export const ARROWS_AND_ENDS = [...ARROWS, 'Home', 'End'];

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
