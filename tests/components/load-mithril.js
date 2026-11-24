// Evaluate the vendored Mithril file and return it. The file is a plain script
// that sets `window.m`, or `module.exports` when a `module` exists.
import source from '@ui/static/vendor/mithril.js?raw';

export function loadMithril() {
  const module = { exports: {} };
  new Function('module', source)(module);
  return module.exports;
}
