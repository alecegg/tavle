// Markup builders and readers for the enhance_table tests. Shared by enhance_table*.test.js.
import { enhanceTables } from '@ui/static/table.js';
import { stubBox } from './stub-layout.js';

const HEAD = '<thead><tr><th>Name</th><th>Qty</th></tr></thead>';
export const td = (text, attrs = '') => `<td${attrs}>${text}</td>`;
export const tr = (...cells) => `<tr>${cells.join('')}</tr>`;
export const rowsNamed = (names) => names.map((name, i) => tr(td(name), td(String(i + 1))));
export const rowsOf = (count) => rowsNamed(Array.from({ length: count }, (_, i) => `Row ${i + 1}`));
export const groupBody = (title, names) =>
  `<tbody><tr class="vb-group-head"><td>${title}</td></tr>${rowsNamed(names).join('')}</tbody>`;

// A table inside a scroll region (the toolbar lives there) unless `scroll` is false.
export function tableHtml({ rows = rowsOf(5), bodies, head = HEAD, cls = 'vb-table', attrs = '', scroll = true } = {}) {
  const body = bodies ?? `<tbody>${rows.join('')}</tbody>`;
  const html = `<table class="${cls}"${attrs}>${head}${body}</table>`;
  return scroll ? `<div class="vb-scroll">${html}</div>` : html;
}

// Mounts html, stubs the scroll region through `prepare`, then enhances the block.
export function mount(html, prepare = () => {}) {
  const block = document.createElement('div');
  block.innerHTML = html;
  document.body.append(block);
  prepare(block.querySelector('.vb-scroll'));
  enhanceTables(block);
  return block;
}

// A region of the given box whose scroll position the test can move.
export function scrollRegion(width, scrollWidth) {
  return (region) => {
    stubBox(region, { width, height: 50 });
    const position = { scrollLeft: 0, scrollTop: 0 };
    Object.defineProperties(region, {
      scrollWidth: { configurable: true, value: scrollWidth },
      scrollLeft: {
        configurable: true,
        get: () => position.scrollLeft,
        set: (value) => {
          position.scrollLeft = value;
        }
      },
      scrollTop: {
        configurable: true,
        get: () => position.scrollTop,
        set: (value) => {
          position.scrollTop = value;
        }
      }
    });
  };
}

export const table = (block) => block.querySelector('table');
export const visibleRows = (block) => Array.from(block.querySelectorAll('tbody tr')).filter((row) => !row.hidden);
export const cellsIn = (block, column) => visibleRows(block).map((row) => row.cells[column].textContent);
export const bodyRows = (block, index) =>
  Array.from(block.querySelectorAll('tbody')[index].rows, (row) => row.cells[0].textContent);
export const headerButtons = (block) => block.querySelectorAll('thead th button');
export const ariaSorts = (block) =>
  Array.from(block.querySelectorAll('thead th'), (th) => th.getAttribute('aria-sort'));
export const sortBy = (block, column) => block.querySelectorAll('thead th')[column].querySelector('button').click();
export const type = (input, value) => {
  input.value = value;
  input.dispatchEvent(new Event('input'));
};

// Each test starts from an empty page with no media query match.
export function resetTableDom() {
  document.body.replaceChildren();
  vi.restoreAllMocks();
  delete window.matchMedia;
}

export function stubMatchMedia(matches = false) {
  window.matchMedia = vi.fn(() => ({ matches }));
}
