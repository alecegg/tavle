// Host component runtime. One hydration loop keyed by `data-component`, one
// shared `$` form-state helper, one answer bridge (`postAnswer`) using the page
// token. Component props arrive only as a `data-props` attribute (JSON, escaped
// by the server); they are parsed with JSON.parse, then reduced to a per-
// component whitelist of keys and types. All text goes through textContent; no
// inline script, no eval, no HTML built from data.
//
// Loaded as a classic deferred script (the page shell and static map are
// owned by other files). It only defines `tavlePageParts.recap(tree, ctx)`; each mounted
// page gets its own helpers in `ctx.tavle` (and `window.tavle` for the document page).
(globalThis.tavlePageParts ||= {}).recap = (tree, ctx) => {
  'use strict';
  const page = tree.querySelector('main[data-role="page"]');
  if (!page) return;
  const publish = (helpers) => {
    ctx.tavle = Object.freeze(helpers);
    if (tree === document) window.tavle = ctx.tavle;
  };

  const { readProps, classifyUrl, safeUrl, formState, register, hydrate, mountInputs, setNote } = globalThis.tavlePageParts.inputRuntime(tree, ctx);

  // ---- answer bridge ----------------------------------------------------------

  // `item` = { kind, id, anchor }. Input components post one unified row
  // `{ kind: 'answer', item, value, text, anchor }`, validated by the server
  // against the component's own props. A recap `drift` judgment is page state,
  // not an answer, and keeps its own row. Returns true when stored; a failure
  // is written to `note` (a { container, selector } pair).
  async function postAnswer(item, value, text, note) {
    const apiBase = ctx.apiBase;
    const headers = apiBase
      ? { 'Content-Type': 'application/json' }
      : { 'Content-Type': 'application/json', [globalThis.tavlePageParts.tokenHeader]: ctx.token };
    const payload = item.kind === 'drift'
      ? { anchor: item.anchor, kind: 'drift', item: item.id, verdict: value, text: text || '' }
      : { anchor: item.anchor, kind: 'answer', item: item.id, value, text: text || '' };
    const report = (message) => note && setNote(note.container, note.selector, message);
    report('');
    try {
      const response = await fetch(apiBase + '/comments' + ctx.apiQuery, { method: 'POST', headers, body: JSON.stringify(payload) });
      if (response.ok) return true;
      report('Not saved (' + response.status + ').');
    } catch (error) {
      report('Not saved: server unreachable.');
    }
    return false;
  }

  ctx.answer = (blockId, value, text) => {
    const entry = tree.querySelector(`[data-item="${CSS.escape(blockId)}"]`);
    const root = entry && entry.closest('[data-component]');
    const block = entry && entry.closest('.block');
    if (!root || !block) return false;
    const note = { container: root, selector: '.' + root.dataset.component + '-error' };
    return postAnswer({ kind: 'answer', id: blockId, anchor: block.dataset.anchor }, value, text, note);
  };
  publish({ readProps, classifyUrl, safeUrl, formState, postAnswer, register, hydrate });

  // ---- built-in components: recap drift buttons and decision verdicts ---------

  function itemOf(kind, entry) {
    const block = entry.closest('.block');
    return block ? { kind, id: entry.dataset.item, anchor: block.dataset.anchor } : null;
  }

  async function judge(button) {
    const recap = button.closest('.recap');
    const entry = button.closest('.recap-item');
    const item = recap && entry && itemOf('drift', entry);
    if (!item) return;
    const verdict = button.dataset.verdict;
    if (!(await postAnswer(item, verdict, '', { container: recap, selector: '.recap-error' }))) return;
    entry.querySelector('.recap-state').textContent = verdict;
    entry.dataset.verdict = verdict;
  }

  // Shows the stored latest answer of each decision: the thread rows carry it,
  // so an answer given elsewhere (the host's panel) reaches this page too.
  // One rule: a stored row is applied once, by id. A row already on the page when
  // this page answered is older than that answer and never overwrites it.
  const applied = new Set();

  function syncDecisions() {
    for (const entry of tree.querySelectorAll('.decision-item')) {
      const latest = tree.querySelector(`.thread[data-latest="true"][data-item="${CSS.escape(entry.dataset.item)}"]`);
      if (!latest || applied.has(latest.dataset.id)) continue;
      applied.add(latest.dataset.id);
      if (!latest.dataset.value) continue;
      entry.querySelector('.decision-state').textContent = latest.dataset.value;
      entry.dataset.verdict = latest.dataset.value;
    }
  }

  function markRowsOlder(item) {
    for (const row of tree.querySelectorAll(`.thread[data-item="${CSS.escape(item)}"]`)) applied.add(row.dataset.id);
  }

  async function decide(entry, verdict, text) {
    const decision = entry.closest('.decision');
    const item = decision && itemOf('decision', entry);
    if (!item || (entry.dataset.verdict === verdict && !text)) return;
    const controls = entry.querySelectorAll('button');
    markRowsOlder(entry.dataset.item);
    controls.forEach((control) => { control.disabled = true; });
    const saved = await postAnswer(item, verdict, text, { container: decision, selector: '.decision-error' });
    controls.forEach((control) => { control.disabled = false; });
    if (!saved) return;
    entry.querySelector('.decision-state').textContent = verdict;
    entry.dataset.verdict = verdict;
    const field = entry.querySelector('.decision-comment');
    if (field) field.hidden = true;
  }

  function chooseDecision(button) {
    const entry = button.closest('.decision-item');
    if (!entry) return;
    if (button.dataset.verdict !== 'commented') return decide(entry, button.dataset.verdict, '');
    const field = entry.querySelector('.decision-comment');
    if (!field) return;
    field.hidden = false;
    const area = field.querySelector('.decision-text');
    if (area) area.focus();
  }

  function sendComment(button) {
    const entry = button.closest('.decision-item');
    const area = entry && entry.querySelector('.decision-text');
    if (!area) return;
    if (!area.value.trim()) return setNote(entry.closest('.decision'), '.decision-error', 'A comment needs text.');
    decide(entry, 'commented', area.value);
  }

  publish({ ...ctx.tavle, inputs: ctx.inputs });
  mountInputs();

  // One delegated click handler: it keeps working when app.js swaps blocks.
  register('answers', {
    hydrate(root) {
      root.addEventListener('click', (event) => {
        const target = event.target instanceof Element ? event.target : null;
        const verdict = target && target.closest('.recap-verdict');
        if (verdict) return judge(verdict);
        const choice = target && target.closest('.decision-verdict');
        if (choice) return chooseDecision(choice);
        const send = target && target.closest('.decision-send');
        if (send) sendComment(send);
      });
    },
  });
  // Temporary: the page root carries no `data-component` because server markup
  // is not emitted yet; the assembler should write it, then drop this line.
  page.dataset.component = 'answers';
  const update = () => { hydrate(tree); syncDecisions(); };
  update();
  const observer = new MutationObserver(update);
  observer.observe(page, { childList: true, subtree: true });
  return () => observer.disconnect();
};
