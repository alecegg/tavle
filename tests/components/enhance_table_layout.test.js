// Data tables: done rows, totals, the scroll region, stack tables and relations.
import { stubBox } from './stub-layout.js';
import {
  stubMatchMedia,
  resetTableDom,
  mount,
  scrollRegion,
  tableHtml,
  rowsOf,
  rowsNamed,
  table,
  tr,
  td,
  visibleRows,
  cellsIn,
  ariaSorts,
  sortBy
} from './table-fixture.js';

beforeEach(() => stubMatchMedia());
afterEach(resetTableDom);

describe('done rows and totals', () => {
  const doneRow = (name) => `<tr data-done="true">${td(name)}${td('1')}</tr>`;

  it.each([' data-hide-done', ' data-hide-done="false"'])('starts with Hide done off for %s', (attrs) => {
    const block = mount(tableHtml({ rows: rowsOf(3), attrs }));
    expect(block.querySelector('.vb-hide-done input').checked).toBe(false);
    expect(visibleRows(block)).toHaveLength(3);
  });

  it('hides done rows from the switch and counts them', () => {
    const block = mount(
      tableHtml({ rows: [doneRow('a'), doneRow('b'), tr(td('c'), td('1'))], attrs: ' data-hide-done="true"' })
    );
    const input = block.querySelector('.vb-hide-done input');
    const status = block.querySelector('.vb-done-status');
    expect(input.checked).toBe(true);
    expect(cellsIn(block, 0)).toEqual(['c']);
    expect(status.textContent).toBe('2 done hidden');
    input.click();
    expect(visibleRows(block)).toHaveLength(3);
    expect(status.textContent).toBe('');
    input.click();
    expect(cellsIn(block, 0)).toEqual(['c']);
    expect(status.textContent).toBe('2 done hidden');
  });

  it('sums data-total and data-progress-done into a total line', () => {
    const rows = [
      tr(td('a'), td('1', ' data-total="4" data-progress-done="1"')),
      tr(td('b'), td('2', ' data-total="6" data-progress-done="2"'))
    ];
    const line = mount(tableHtml({ rows })).querySelector('.vb-total-progress');
    expect(line.textContent.trim()).toBe('Total: 3 of 10');
    expect(line.querySelector('progress').value).toBe(3);
    expect(line.querySelector('progress').max).toBe(10);
  });
});

describe('scroll region', () => {
  it('shows the scroll hint only while the table is wider than its region', () => {
    const wide = mount(tableHtml({ rows: rowsOf(2) }), scrollRegion(100, 300));
    expect(wide.querySelector('.vb-scrollhint').hidden).toBe(false);
    const narrow = mount(tableHtml({ rows: rowsOf(2) }), scrollRegion(100, 100));
    expect(narrow.querySelector('.vb-scrollhint').hidden).toBe(true);
  });

  it('fades each edge the table continues past', () => {
    const block = mount(tableHtml({ rows: rowsOf(2) }), scrollRegion(100, 300));
    const region = block.querySelector('.vb-scroll');
    const edgesOf = () => ['vb-more-start', 'vb-more-end'].filter((name) => region.classList.contains(name));
    expect(edgesOf()).toEqual(['vb-more-end']);
    region.scrollLeft = 150;
    region.dispatchEvent(new Event('scroll'));
    expect(edgesOf()).toEqual(['vb-more-start', 'vb-more-end']);
    region.scrollLeft = 200;
    region.dispatchEvent(new Event('scroll'));
    expect(edgesOf()).toEqual(['vb-more-start']);
  });

  it('scrolls sideways to a focused cell and never vertically', () => {
    const block = mount(tableHtml({ rows: rowsOf(2) }), scrollRegion(100, 300));
    const region = block.querySelector('.vb-scroll');
    const cell = block.querySelector('tbody td');
    stubBox(cell, { left: 150, top: 500, width: 20, height: 20 });
    cell.dispatchEvent(new Event('focusin', { bubbles: true }));
    expect(region.scrollLeft).toBe(74);
    expect(region.scrollTop).toBe(0);
    region.dispatchEvent(new Event('focusin', { bubbles: true }));
    expect(region.scrollLeft).toBe(74);
  });
});

describe('stack tables', () => {
  const STACK = 'vb-table vb-table-stack';

  it('adds vb-cards when the media query matches', () => {
    stubMatchMedia(true);
    const block = mount(tableHtml({ cls: STACK, rows: rowsOf(5) }), scrollRegion(300, 300));
    expect(table(block).classList.contains('vb-cards')).toBe(true);
    expect(window.matchMedia).toHaveBeenCalledWith('(max-width: 40rem)');
  });

  it('adds vb-cards when the full-width probe overflows, and removes the probe', () => {
    vi.spyOn(Element.prototype, 'scrollWidth', 'get').mockImplementation(function probeWidth() {
      return this.style.inlineSize === 'max-content' ? 900 : 0;
    });
    const block = mount(tableHtml({ cls: STACK, rows: rowsOf(5) }), scrollRegion(300, 300));
    expect(table(block).classList.contains('vb-cards')).toBe(true);
    expect(block.querySelectorAll('table')).toHaveLength(1);
  });

  it('keeps the table as a table when it fits', () => {
    const block = mount(tableHtml({ cls: STACK, rows: rowsOf(5) }), scrollRegion(300, 300));
    expect(table(block).classList.contains('vb-cards')).toBe(false);
  });

  it('adds a Sort by select kept in step with the header clicks', () => {
    const block = mount(tableHtml({ cls: STACK, rows: rowsNamed(['b', 'a', 'c', 'e', 'd']) }), scrollRegion(300, 300));
    const select = block.querySelector('.vb-sortselect');
    expect(Array.from(select.options, (option) => option.value)).toEqual(['', '0:1', '0:-1', '1:1', '1:-1']);
    sortBy(block, 1);
    expect(select.value).toBe('1:1');
    select.value = '0:-1';
    select.dispatchEvent(new Event('change'));
    expect(ariaSorts(block)).toEqual(['descending', 'none']);
    expect(cellsIn(block, 0)).toEqual(['e', 'd', 'c', 'b', 'a']);
    select.value = '';
    select.dispatchEvent(new Event('change'));
    expect(ariaSorts(block)).toEqual(['none', 'none']);
    expect(cellsIn(block, 0)).toEqual(['b', 'a', 'c', 'e', 'd']);
  });

  it('adds no Sort by select to a plain table', () => {
    const block = mount(tableHtml({ rows: rowsOf(5) }), scrollRegion(300, 300));
    expect(block.querySelector('.vb-sortselect')).toBeNull();
  });
});

describe('relations', () => {
  it('toggles the list behind a Relations button', () => {
    const block = mount('<ul class="vb-relations"><li>a</li><li>b</li></ul>');
    const list = block.querySelector('.vb-relations');
    const button = block.querySelector('.vb-toggle');
    expect(button.textContent).toBe('Relations (2)');
    expect(button.getAttribute('aria-expanded')).toBe('true');
    button.click();
    expect(list.hidden).toBe(true);
    expect(button.getAttribute('aria-expanded')).toBe('false');
    button.click();
    expect(list.hidden).toBe(false);
  });
});
