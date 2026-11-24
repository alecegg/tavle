// The component registry as the bundle builds it: every file in static/components
// except mount.js, each as an object of its exports.
import { loadMithril } from './load-mithril.js';

const files = import.meta.glob('@ui/static/components/*.js', { eager: true });

export function loadComponents() {
  const registry = {};
  for (const [path, exports] of Object.entries(files)) {
    const name = path.split('/').pop().replace('.js', '');
    if (name !== 'mount') registry[name] = exports;
  }
  return { m: loadMithril(), components: registry };
}
