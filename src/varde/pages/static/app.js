// Comments, editing and live refresh for one mounted page. It only defines
// `vardePageParts.app(tree, ctx)` and `vardePageParts.mount`; nothing runs at load.
// `tree` is the document or the shadow root the page lives in; `ctx` is the mount's state.
(globalThis.vardePageParts ||= {}).app = (tree, ctx) => {
  'use strict';
  const tokenMeta = () => tree.querySelector('meta[name="varde-token"]');
  // Set when serve hosts the page: posts go to `{apiBase}/comments`, no token,
  // refresh reads `pageUrl`, and there is no live event stream or editing.
  const apiBase = ctx.apiBase;
  const pageUrl = ctx.pageUrl;
  const inline = tree !== document; // the host page owns refresh timing and the event stream
  const postHeaders = () => apiBase
    ? { 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json', 'X-Varde-Token': ctx.token };
  const root = () => tree.querySelector('main[data-role="page"]');
  const composers = new Map(); // anchor -> draft text kept across refreshes
  let generation = 0;
  const serializer = new XMLSerializer();
  const signature = (node) => serializer.serializeToString(node);
  const threadHtml = () => Array.from(root().querySelectorAll(':scope > .thread, :scope > .orphans'), (n) => signature(n)).join('');
  let threadSignature = threadHtml();
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
    const actions = document.createElement('div');
    actions.className = 'actions';
    const submit = document.createElement('button');
    submit.type = 'button';
    submit.className = 'primary';
    submit.textContent = 'Send';
    submit.addEventListener('click', () => send(block, form, textarea));
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = 'Cancel';
    cancel.addEventListener('click', () => {
      composers.delete(anchor);
      form.remove();
    });
    const error = document.createElement('p');
    error.className = 'error';
    actions.append(submit, cancel);
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

  // Smallest differing middle of two texts, widened by one character when empty.
  function changedSpan(before, after) {
    let head = 0;
    while (head < before.length && head < after.length && before[head] === after[head]) head++;
    let tail = 0;
    while (
      tail < before.length - head &&
      tail < after.length - head &&
      before[before.length - 1 - tail] === after[after.length - 1 - tail]
    ) tail++;
    let start = head;
    let endBefore = before.length - tail;
    let endAfter = after.length - tail;
    if (start === endBefore) {
      if (start > 0) start--;
      else if (endBefore < before.length) { endBefore++; endAfter++; }
    }
    return { quote: before.slice(start, endBefore), replacement: after.slice(start, endAfter) };
  }

  async function saveEditor(block, form, textarea, loaded, mode) {
    const text = textarea.value;
    let failure;
    if (mode === 'edit') {
      failure = await post('/edit', { anchor: block.dataset.anchor, base_hash: loaded.hash, new_source: text });
    } else {
      const span = changedSpan(loaded.source, text);
      if (!span.quote) return showError(form, 'Change some text first.');
      failure = await post('/comments', {
        anchor: block.dataset.anchor, kind: 'suggestion', quote: span.quote, replacement: span.replacement, text: '',
      });
    }
    if (failure) return showError(form, failure);
    form.remove();
    refresh();
  }

  async function openEditor(block, mode, offset) {
    const anchor = block.dataset.anchor;
    const selector = '.editor[data-mode="' + mode + '"][data-anchor="' + CSS.escape(anchor) + '"]';
    if (root().querySelector(selector)) return;
    let loaded;
    try {
      const response = await fetch('/block?anchor=' + encodeURIComponent(anchor), { cache: 'no-store' });
      if (!response.ok) return;
      loaded = await response.json();
    } catch (error) {
      return;
    }
    const form = document.createElement('div');
    form.className = 'composer editor';
    form.dataset.anchor = anchor;
    form.dataset.mode = mode;
    const textarea = document.createElement('textarea');
    textarea.setAttribute('aria-label', mode === 'edit' ? 'Block source' : 'Suggested source');
    textarea.value = loaded.source;
    const actions = document.createElement('div');
    actions.className = 'actions';
    const submit = document.createElement('button');
    submit.type = 'button';
    submit.className = 'primary';
    submit.textContent = mode === 'edit' ? 'Save' : 'Suggest';
    submit.addEventListener('click', () => saveEditor(block, form, textarea, loaded, mode));
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = 'Cancel';
    cancel.addEventListener('click', () => form.remove());
    const error = document.createElement('p');
    error.className = 'error';
    actions.append(submit, cancel);
    form.append(textarea, actions, error);
    mountForm(block, form, offset);
    textarea.focus({ preventScroll: true });
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
    for (const thread of scope.querySelectorAll('.thread:not(.orphan)')) {
      const block = blockFor(thread.dataset.anchor);
      if (block) groupEnd(block).after(thread);
    }
    for (const [anchor, draft] of composers) {
      const block = blockFor(anchor);
      if (block) openComposer(block, draft);
    }
  }

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
    for (const next of incoming) {
      const block = current.get(next.dataset.anchor);
      if (!block) {
        const added = document.importNode(next, true);
        added.classList.add('changed');
        if (cursor) root().insertBefore(added, cursor);
        else appendBlock(added);
        continue;
      }
      if (block !== cursor) root().insertBefore(block, cursor);
      else cursor = nextBlock(block);
      if (block.dataset.hash === next.dataset.hash) continue;
      const replacement = document.importNode(next, true);
      replacement.classList.add('changed');
      block.replaceWith(replacement);
    }
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

  function syncOthers(fresh) {
    const header = root().querySelector(':scope > .doc-header');
    const incomingHeader = fresh.querySelector(':scope > .doc-header');
    if (header && !incomingHeader) header.remove();
    else if (!header && incomingHeader) root().prepend(document.importNode(incomingHeader, true));
    else if (header && signature(header) !== signature(incomingHeader)) {
      header.replaceWith(document.importNode(incomingHeader, true));
    }
    const incoming = Array.from(fresh.querySelectorAll(':scope > .thread, :scope > .orphans'));
    const joined = incoming.map((n) => signature(n)).join('');
    if (joined === threadSignature) return;
    threadSignature = joined;
    for (const old of root().querySelectorAll('.thread, .orphans')) old.remove();
    root().append(...incoming.map((node) => document.importNode(node, true)));
  }

  async function refresh() {
    const mine = ++generation;
    let text;
    try {
      if (ctx.loadPage) {
        text = await ctx.loadPage();
      } else {
        const response = await fetch(pageUrl, { cache: 'no-store' });
        if (!response.ok) return;
        text = await response.text();
      }
    } catch (error) {
      return;
    }
    if (stopped || mine !== generation) return;
    const parsed = new DOMParser().parseFromString(text, 'text/html');
    const fresh = parsed.querySelector('main[data-role="page"]');
    const freshToken = parsed.querySelector('meta[name="varde-token"]');
    if (!fresh || (!apiBase && !freshToken)) return;
    if (!apiBase) ctx.token = freshToken.content;
    if (!apiBase && tokenMeta()) tokenMeta().content = freshToken.content;
    syncBlocks(fresh);
    syncOthers(fresh);
    decorate();
  }

  function scheduleRefresh() {
    clearTimeout(timer);
    timer = setTimeout(refresh, 150);
  }

  ctx.refresh = refresh;
  let menu = null;
  let stopToc = () => {};
  let closeEvents = () => {};
  const stop = () => {
    stopped = true;
    clearTimeout(timer);
    window.removeEventListener('message', onHostMessage);
    closeEvents();
    if (menu) menu.destroy();
    stopToc();
  };
  // The host window posts {type:"varde-refresh"} when the document changes.
  function onHostMessage(event) {
    if (event.origin === location.origin && event.source === window.parent && event.data && event.data.type === 'varde-refresh') scheduleRefresh();
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
// returns { refresh, destroy, varde }. A tree mounts once; `page.js` calls this for any root and
// `mountDocument` is the served page's call.
(globalThis.vardePageParts ||= {}).mount = (tree, opts = {}) => {
  const parts = globalThis.vardePageParts;
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
    varde: null,
  };
  const stops = ['app', 'blocks', 'recap', 'inputs'].map((name) => parts[name] && parts[name](tree, ctx));
  const handle = {
    refresh: () => (ctx.refresh ? ctx.refresh() : Promise.resolve()),
    destroy: () => {
      mounted.delete(tree);
      stops.forEach((stop) => stop && stop());
    },
    get varde() { return ctx.varde; },
  };
  mounted.set(tree, handle);
  return handle;
};

// The served page: options come from the body's data attributes and the token meta, as the
// page shell writes them.
globalThis.vardePageParts.mountDocument = () => {
  const meta = document.querySelector('meta[name="varde-token"]');
  return globalThis.vardePageParts.mount(document, {
    apiBase: document.body.dataset.apiBase,
    pageUrl: document.body.dataset.pageUrl,
    token: meta ? meta.content : '',
  });
};
