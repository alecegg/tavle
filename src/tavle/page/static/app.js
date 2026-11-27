// Comments, editing and live refresh for one mounted page. It only defines
// `tavlePageParts.app(tree, ctx)` and `tavlePageParts.mount`; nothing runs at load.
// `tree` is the document or the shadow root the page lives in; `ctx` is the mount's state.
(globalThis.tavlePageParts ||= {}).tokenHeader = "X-Tavle-Token";
globalThis.tavlePageParts.app = (tree, ctx) => {
  'use strict';
  const tokenMeta = () => tree.querySelector('meta[name="tavle-token"]');
  // Set when serve hosts the page: posts go to `{apiBase}/comments`, no token,
  // refresh reads `pageUrl`, and there is no live event stream or editing.
  const apiBase = ctx.apiBase;
  const pageUrl = ctx.pageUrl;
  const inline = tree !== document; // the host page owns refresh timing and the event stream
  // The send and cancel buttons of an inline composer, and the error line that goes below them.
  function composerActions(label, onSend, onCancel) {
    const actions = document.createElement('div');
    actions.className = 'actions';
    const submit = document.createElement('button');
    submit.type = 'button';
    submit.className = 'primary';
    submit.textContent = label;
    submit.addEventListener('click', onSend);
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = 'Cancel';
    cancel.addEventListener('click', onCancel);
    actions.append(submit, cancel);
    const error = document.createElement('p');
    error.className = 'error';
    return { actions, error };
  }
  const postHeaders = () => apiBase
    ? { 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json', [globalThis.tavlePageParts.tokenHeader]: ctx.token };
  const root = () => tree.querySelector('main[data-role="page"]');
  const composers = new Map(); // anchor -> draft text kept across refreshes
  let generation = 0;
  let sync;
  const serializer = new XMLSerializer();
  const signature = (node) => serializer.serializeToString(node);
  const threadHtml = () => Array.from(root().querySelectorAll(':scope > .thread, :scope > .orphans'), (n) => signature(n)).join('');
  const threadSignature = threadHtml();
  let timer = null;
  let mountMenu = null; // set once menu.js has loaded
  let stopped = false;

  function blockFor(anchor) {
    for (const block of root().querySelectorAll('.block')) {
      if (block.dataset.anchor === anchor) return block;
    }
    return null;
  }

  function groupEnd(block) {
    let last = block;
    while (last.nextElementSibling && last.nextElementSibling.classList.contains('thread')) {
      last = last.nextElementSibling;
    }
    return last;
  }

  function quoteOf(block) {
    return block.textContent.replace(/\s+/g, ' ').trim().slice(0, 80);
  }

  function showError(form, message) {
    form.querySelector('.error').textContent = message;
  }

  async function send(block, form, textarea) {
    const text = textarea.value;
    if (!text.trim()) return showError(form, 'Write a comment first.');
    const body = JSON.stringify({ anchor: block.dataset.anchor, quote: quoteOf(block), text });
    const headers = postHeaders();
    try {
      const response = await fetch(apiBase + '/comments' + ctx.apiQuery, { method: 'POST', headers, body });
      if (!response.ok) return showError(form, 'Not saved (' + response.status + ').');
    } catch (error) {
      return showError(form, 'Not saved: server unreachable.');
    }
    composers.delete(block.dataset.anchor);
    form.remove();
    refresh();
  }

  // Next to the block, or (after a tap) floating over it around the tap point and inside the screen,
  // so a block taller than the screen needs no scroll to write and nothing below it moves.
  function mountForm(block, form, offset) {
    if (offset === null || offset === undefined) return groupEnd(block).after(form);
    form.classList.add('floating');
    block.append(form);
    const room = window.innerHeight - form.offsetHeight - 8;
    const rect = block.getBoundingClientRect();
    const top = Math.min(Math.max(rect.top + offset - form.offsetHeight / 2, 8), room);
    form.style.top = top - rect.top + 'px';
  }

  function openComposer(block, draft, offset) {
    const anchor = block.dataset.anchor;
    const open = root().querySelector('.composer[data-anchor="' + CSS.escape(anchor) + '"]');
    if (open) return open.querySelector('textarea').focus({ preventScroll: true });
    const form = document.createElement('div');
    form.className = 'composer';
    form.dataset.anchor = anchor;
    const textarea = document.createElement('textarea');
    textarea.setAttribute('aria-label', 'Comment');
    textarea.value = draft || '';
    textarea.addEventListener('input', () => composers.set(anchor, textarea.value));
    const { actions, error } = composerActions('Send', () => send(block, form, textarea), () => {
      composers.delete(anchor);
      form.remove();
    });
    form.append(textarea, actions, error);
    mountForm(block, form, offset);
    if (draft === undefined) textarea.focus({ preventScroll: true });
  }

  async function post(path, payload) {
    const headers = postHeaders();
    try {
      const response = await fetch(apiBase + path + ctx.apiQuery, { method: 'POST', headers, body: JSON.stringify(payload) });
      if (response.ok) return '';
      if (response.status === 409) return 'The block changed; wait for the refresh and retry.';
      return 'Not saved (' + response.status + ').';
    } catch (error) {
      return 'Not saved: server unreachable.';
    }
  }

  async function openEditor(...args) {
    const { createEditor } = await import('./editor.js');
    return createEditor({ root, post, showError, refresh, mountForm, composerActions })(...args);
  }

  async function accept(thread, button) {
    const block = blockFor(thread.dataset.anchor);
    if (!block) return;
    const failure = await post('/accept', { comment_id: thread.dataset.id, base_hash: block.dataset.hash });
    if (failure) button.textContent = failure;
    else refresh();
  }

  function addButton(parent, className, label, onClick) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = label;
    button.addEventListener('click', onClick);
    parent.append(button);
  }

  function decorate() {
    const scope = root();
    for (const block of mountMenu && !ctx.readOnly ? scope.querySelectorAll('.block') : []) {
      mountMenu(block, { comment: openComposer, edit: openEditor, readOnly: Boolean(apiBase) });
    }
    const suggestions = apiBase ? [] : scope.querySelectorAll('.thread[data-kind="suggestion"]:not(.resolved)');
    for (const thread of suggestions) {
      if (thread.querySelector(':scope > .accept-btn')) continue;
      addButton(thread, 'accept-btn', 'Accept', (event) => accept(thread, event.currentTarget));
    }
    restoreThreads(scope);
  }

  function restoreThreads(scope) {
    for (const thread of scope.querySelectorAll('.thread:not(.orphan)')) {
      const block = blockFor(thread.dataset.anchor);
      if (block) groupEnd(block).after(thread);
    }
    for (const [anchor, draft] of composers) {
      const block = blockFor(anchor);
      if (block) openComposer(block, draft);
    }
  }

  async function loadPage() {
    try {
      if (ctx.loadPage) return await ctx.loadPage();
      const response = await fetch(pageUrl, { cache: 'no-store' });
      return response.ok ? await response.text() : null;
    } catch (error) {
      return null;
    }
  }

  function updateToken(freshToken) {
    if (apiBase) return;
    ctx.token = freshToken.content;
    if (tokenMeta()) tokenMeta().content = freshToken.content;
  }

  async function refresh() {
    const mine = ++generation;
    const text = await loadPage();
    if (text === null) return;
    if (stopped || mine !== generation) return;
    const parsed = new DOMParser().parseFromString(text, 'text/html');
    const fresh = parsed.querySelector('main[data-role="page"]');
    const freshToken = parsed.querySelector('meta[name="tavle-token"]');
    if (!fresh || (!apiBase && !freshToken)) return;
    updateToken(freshToken);
    const { createSync, keepFocus } = await import('./sync.js');
    if (stopped || mine !== generation) return;
    sync ||= createSync(root, groupEnd, signature, threadSignature);
    keepFocus(() => {
      sync.syncBlocks(fresh);
      sync.syncOthers(fresh);
      decorate();
    });
  }

  function scheduleRefresh() {
    clearTimeout(timer);
    timer = setTimeout(refresh, 150);
  }

  ctx.refresh = refresh;
  let menu = null;
  let stopToc = () => {};
  let stopSections = () => {};
  let closeEvents = () => {};
  const stop = () => {
    stopped = true;
    clearTimeout(timer);
    window.removeEventListener('message', onHostMessage);
    closeEvents();
    if (menu) menu.destroy();
    stopToc();
    stopSections();
  };
  // The host window posts {type:"tavle-refresh"} when the document changes.
  function onHostMessage(event) {
    if (event.origin === location.origin && event.source === window.parent && event.data && event.data.type === 'tavle-refresh') scheduleRefresh();
  }
  decorate();
  import('./menu.js').then((module) => {
    if (stopped) return;
    menu = module.createMenu(tree);
    mountMenu = menu.mountMenu;
    decorate();
  });
  import('./toc.js').then((toc) => {
    if (!stopped) stopToc = toc.mountToc(tree);
  });
  if (root()?.dataset.sections) {
    import('./sections.js').then((sections) => {
      if (!stopped) stopSections = sections.mountSections(tree);
    });
  }
  if (inline) return stop;
  window.addEventListener('message', onHostMessage);
  if (!apiBase) {
    const events = new EventSource('/events');
    events.addEventListener('update', scheduleRefresh);
    events.addEventListener('open', scheduleRefresh);
    closeEvents = () => events.close();
  }
  return stop;
};

// Runs the page parts (app, blocks, recap, inputs) on `tree` with one shared `ctx`, and
// returns { refresh, destroy, tavle }. A tree mounts once; `page.js` calls this for any root and
// `mountDocument` is the served page's call.
(globalThis.tavlePageParts ||= {}).mount = (tree, opts = {}) => {
  const parts = globalThis.tavlePageParts;
  const mounted = (parts.mounted ||= new WeakMap());
  if (mounted.has(tree)) return mounted.get(tree);
  const ctx = {
    apiBase: opts.apiBase || '',
    apiQuery: opts.apiQuery || '', // appended to every apiBase call, e.g. '?project=...'
    pageUrl: opts.pageUrl || '/',
    token: opts.token || '',
    loadPage: opts.refresh || null, // optional () => Promise<string>: the page's fresh HTML
    readOnly: Boolean(opts.readOnly), // no block menu, so nothing to comment on or edit
    refresh: null,
    tavle: null,
  };
  const stops = ['app', 'blocks', 'recap', 'inputs'].map((name) => parts[name] && parts[name](tree, ctx));
  const handle = {
    refresh: () => (ctx.refresh ? ctx.refresh() : Promise.resolve()),
    destroy: () => {
      mounted.delete(tree);
      stops.forEach((stop) => stop && stop());
    },
    get tavle() { return ctx.tavle; },
  };
  mounted.set(tree, handle);
  return handle;
};

// The served page: options come from the body's data attributes and the token meta, as the
// page shell writes them.
globalThis.tavlePageParts.mountDocument = () => {
  const meta = document.querySelector('meta[name="tavle-token"]');
  return globalThis.tavlePageParts.mount(document, {
    apiBase: document.body.dataset.apiBase,
    pageUrl: document.body.dataset.pageUrl,
    token: meta ? meta.content : '',
  });
};
