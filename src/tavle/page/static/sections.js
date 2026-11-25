// Collapsible h2 sections for pages whose front matter sets `sections: collapsible`.
// Section state lives in sessionStorage and is reapplied when live refresh replaces blocks.
const key = (id) => `tavle-section:${location.pathname}:${id}`;
const read = (id) => { try { return sessionStorage.getItem(key(id)) === 'closed'; } catch { return false; } };
const write = (id, closed) => { try { sessionStorage.setItem(key(id), closed ? 'closed' : 'open'); } catch {} };
const isSectionEnd = (block) => block.matches('.block.heading') && block.querySelector(':scope > h1, :scope > h2');

function toggleFor(heading, remount) {
  let button = heading.querySelector('button[data-section-toggle]');
  if (button) return button;
  button = document.createElement('button');
  button.type = 'button';
  button.dataset.sectionToggle = '';
  button.append(...heading.childNodes);
  heading.append(button);
  button.addEventListener('click', () => { write(heading.id, button.getAttribute('aria-expanded') === 'true'); remount(); });
  return button;
}

function applySection(blocks, index, closed) {
  for (const sibling of blocks.slice(index + 1)) {
    if (isSectionEnd(sibling)) return;
    sibling.hidden = closed;
  }
}

/** Mount toggles under `tree` (a document or an element holding the page main); returns a stop function. */
export function mountSections(tree) {
  let printing = false;
  function mount() {
    tree.querySelectorAll('main[data-sections="collapsible"]').forEach((main) => {
      const blocks = Array.from(main.children);
      blocks.forEach((block, index) => {
        const heading = block.matches('.block.heading') && block.querySelector(':scope > h2');
        if (!heading) return;
        const closed = !printing && read(heading.id);
        toggleFor(heading, mount).setAttribute('aria-expanded', String(!closed));
        applySection(blocks, index, closed);
      });
    });
  }
  const beforePrint = () => { printing = true; mount(); };
  const afterPrint = () => { printing = false; mount(); };
  const observer = new MutationObserver(mount);
  mount();
  observer.observe(tree, { childList: true, subtree: true });
  window.addEventListener('beforeprint', beforePrint);
  window.addEventListener('afterprint', afterPrint);
  return () => {
    observer.disconnect();
    window.removeEventListener('beforeprint', beforePrint);
    window.removeEventListener('afterprint', afterPrint);
  };
}
