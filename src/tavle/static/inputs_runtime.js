import { readFields } from './inputs_fields.js';
import { mountInputs as mountInputWidgets } from './inputs_widgets.js';

// Component props, state and input hydration, independent of the page host.
(globalThis.vardePageParts ||= {}).inputRuntime = (tree, ctx) => {
  'use strict';
  // ---- props: parse, then whitelist -----------------------------------------

  // Port of pages/render.py classify_url; tests/docs/fixtures/url-vectors.json is
  // run against both, so they cannot drift. Returns 'link', 'relative' or 'text'.
  const SAFE_URL = /^(https?:\/\/[A-Za-z0-9\-._~:/?#[\]@!$&()*+,;=%]+|#[A-Za-z0-9\-._~:/?#%]*)$/;
  // Python `\s` plus the ASCII control range and DEL (not JS `\s`: it differs).
  const STRIP = /[\u0000-\u0020\u007f\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/g;

  // HTML entity decoding like Python html.unescape. A `<title>` is RCDATA: it
  // decodes entities and never builds elements; `<` is escaped so the text
  // cannot close it. Raw NUL is dropped first (the parser would rewrite it).
  function unescapeEntities(text) {
    const clean = text.replace(/\u0000/g, '');
    if (!clean.includes('&')) return clean;
    const markup = '<!doctype html><title>' + clean.replace(/</g, '&lt;') + '</title>';
    const title = new DOMParser().parseFromString(markup, 'text/html').querySelector('title');
    return title ? title.textContent : clean;
  }

  function classifyUrl(url) {
    const stripped = unescapeEntities(url).replace(STRIP, '');
    if (SAFE_URL.test(url) && stripped === url) return 'link';
    if (!stripped || stripped.startsWith('//') || stripped.startsWith('\\') || stripped.includes('\\')) return 'text';
    const head = stripped.split(/[/?#]/, 1)[0];
    return head.includes(':') || /[^\u0000-\u007f]/.test(stripped) ? 'text' : 'relative';
  }

  // The value when it is a link or relative reference, else null.
  function safeUrl(value) {
    if (typeof value !== 'string') return null;
    return classifyUrl(value) === 'text' ? null : value;
  }

  const TYPES = {
    string: (v) => (typeof v === 'string' ? v : undefined),
    number: (v) => (typeof v === 'number' && Number.isFinite(v) ? v : undefined),
    boolean: (v) => (typeof v === 'boolean' ? v : undefined),
    url: (v) => safeUrl(v) ?? undefined,
    strings: (v) => (Array.isArray(v) && v.every((x) => typeof x === 'string') ? v.slice() : undefined),
    fields: (v) => (Array.isArray(v) && v.length <= 50 ? readFields(v) : undefined),
  };

  // `schema` maps key -> type name above. Unknown keys and wrong types are dropped.
  function readProps(element, schema) {
    const props = {};
    let raw;
    try {
      raw = JSON.parse(element.getAttribute('data-props') || '{}');
    } catch (error) {
      return props;
    }
    if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) return props;
    for (const [key, type] of Object.entries(schema)) {
      if (!Object.prototype.hasOwnProperty.call(raw, key)) continue;
      const value = TYPES[type](raw[key]);
      if (value !== undefined) props[key] = value;
    }
    return props;
  }

  // ---- `$` form state ---------------------------------------------------------

  const values = new Map();
  const watchers = new Map();

  const formState = {
    get: (name) => values.get(name),
    set(name, value) {
      values.set(name, value);
      for (const watcher of watchers.get(name) || []) {
        try {
          watcher(value);
        } catch (error) {
          console.error(error);
        }
      }
    },
    watch(name, watcher) {
      if (!watchers.has(name)) watchers.set(name, new Set());
      watchers.get(name).add(watcher);
      return () => {
        const set = watchers.get(name);
        set.delete(watcher);
        if (!set.size) watchers.delete(name);
      };
    },
  };

  // ---- hydration loop ---------------------------------------------------------

  const registry = new Map();

  // hydrator: { props: schema, hydrate(element, props) }. A component may also
  // hydrate markup the server renders without `data-props`.
  function register(name, hydrator) {
    registry.set(name, hydrator);
  }

  function hydrate(scope) {
    for (const element of scope.querySelectorAll('[data-component]:not([data-hydrated])')) {
      const hydrator = registry.get(element.dataset.component);
      if (!hydrator) continue;
      element.dataset.hydrated = '1';
      hydrator.hydrate(element, readProps(element, hydrator.props || {}));
    }
  }

  // ---- answer port helpers -----------------------------------------------------

  function setNote(container, selector, message) {
    const note = container && container.querySelector(selector);
    if (note) note.textContent = message;
  }

  // Sends the widget `root`'s answer through the host's `ctx.answer` port.
  // Returns true when stored; a page without the port stores nothing.
  async function sendAnswer(root, kind, value, text) {
    if (!ctx.answer) return false;
    const entry = root.querySelector('.' + kind + '-item');
    const block = root.closest('.block');
    if (!entry || !block) return false;
    // Only controls that were live are paused and restored: read-only ones stay off.
    const controls = Array.from(root.querySelectorAll('button, input, select, textarea')).filter((control) => !control.disabled);
    const focused = controls.find((control) => control === tree.activeElement);
    controls.forEach((control) => { control.disabled = true; });
    const saved = await ctx.answer(entry.dataset.item, value, text);
    controls.forEach((control) => { control.disabled = false; });
    if (focused) focused.focus(); // disabling dropped focus to the body
    if (saved) setNote(root, '.' + kind + '-state', 'Sent');
    return saved;
  }

  // Shows `message`, ties it to `control` with aria-describedby and moves focus there.
  function fail(root, kind, message, control) {
    setNote(root, '.' + kind + '-error', message);
    const note = root.querySelector('.' + kind + '-error');
    if (!control) return;
    if (note && note.id) control.setAttribute('aria-describedby', note.id);
    control.focus();
  }

  function onSubmit(root, kind, handler) {
    const form = root.querySelector('form');
    if (!form) return;
    const clear = () => setNote(root, '.' + kind + '-state', '');
    form.addEventListener('input', clear);
    form.addEventListener('change', clear);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      handler(form);
    });
  }

  const mountInputs = () => mountInputWidgets({ register, onSubmit, fail, setNote, sendAnswer });

  ctx.inputs = Object.freeze({ register, hydrate, sendAnswer, onSubmit, fail });
  return { readProps, classifyUrl, safeUrl, formState, register, hydrate, mountInputs, setNote };
};
