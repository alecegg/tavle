// code: adds a Copy button to a code panel. The panel is complete without this script;
// the button copies the raw source (`data-copy`, never the line numbers) and says so in
// a polite live region.
import { control, make, overlayParent } from './dom.js';

const CONFIRM_MS = 2500;

function copyWithTextarea(text, block) {
  const area = make('textarea', 'vd-code-scratch');
  area.value = text;
  area.setAttribute('readonly', '');
  overlayParent(block).append(area);
  area.select();
  let done = false;
  try {
    done = document.execCommand('copy');
  } catch (error) {
    done = false;
  }
  area.remove();
  return done ? Promise.resolve() : Promise.reject(new Error('copy failed'));
}

function writeText(text, block) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text).catch(() => copyWithTextarea(text, block));
  }
  return copyWithTextarea(text, block);
}

export function enhanceCode(block) {
  if (!block.classList.contains('vd-code')) return;
  const head = block.querySelector('.vd-code-head');
  if (!head) return;
  const status = make('span', 'vd-code-status');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  let timer = 0;
  function say(message) {
    status.textContent = message;
    clearTimeout(timer);
    timer = setTimeout(() => { status.textContent = ''; }, CONFIRM_MS);
  }
  const button = control('Copy', () => {
    writeText(block.dataset.copy || '', block).then(
      () => say('Copied \u2713'),
      () => say('Copy failed: select the text instead'),
    );
  }, 'vd-code-copy', 'Copy code');
  head.append(button, status);
}
