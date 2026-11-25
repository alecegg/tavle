export function createEditor({ root, post, showError, refresh, mountForm }) {
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

  return openEditor;
}
