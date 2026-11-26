// Data tables: structure, sorting, filtering and the row cap.
import {
  stubMatchMedia,
  resetTableDom,
  mount,
  tableHtml,
  rowsOf,
  rowsNamed,
  groupBody,
  tr,
  td,
  visibleRows,
  cellsIn,
  bodyRows,
  headerButtons,
  ariaSorts,
  sortBy,
  type
} from './table-fixture.js';

beforeEach(() => stubMatchMedia());
afterEach(resetTableDom);

describe('table structure', () => {
  it('leaves a table without a thead or a tbody alone', () => {
    const noHead = mount(tableHtml({ head: '', rows: rowsOf(9) }));
    const noBody = mount(tableHtml({ bodies: '' }));
    expect(visibleRows(noHead)).toHaveLength(9);
    for (const block of [noHead, noBody]) {
      expect(block.querySelector('.vb-filterbar')).toBeNull();
      expect(block.querySelector('button')).toBeNull();
    }
  });

  it('adds sort buttons from five rows and none at four', () => {
    const five = mount(tableHtml({ rows: rowsOf(5) }));
    expect(headerButtons(five)).toHaveLength(2);
    expect(ariaSorts(five)).toEqual(['none', 'none']);
    const four = mount(tableHtml({ rows: rowsOf(4) }));
    expect(headerButtons(four)).toHaveLength(0);
    expect(ariaSorts(four)).toEqual([null, null]);
  });

  it('puts the toolbar only inside .vb-scroll, though sort buttons still appear', () => {
    const block = mount(tableHtml({ rows: rowsOf(17), scroll: false }));
    expect(headerButtons(block)).toHaveLength(2);
    expect(block.querySelector('.vb-filterbar')).toBeNull();
    expect(block.querySelector('.vb-more')).toBeNull();
  });
});

describe('sorting', () => {
  it('cycles a column ascending, descending, then as authored', () => {
    const block = mount(tableHtml({ rows: rowsNamed(['b', 'a', 'c', 'd', 'e']) }));
    sortBy(block, 0);
    expect(ariaSorts(block)).toEqual(['ascending', 'none']);
    expect(cellsIn(block, 0)).toEqual(['a', 'b', 'c', 'd', 'e']);
    sortBy(block, 0);
    expect(ariaSorts(block)).toEqual(['descending', 'none']);
    expect(cellsIn(block, 0)).toEqual(['e', 'd', 'c', 'b', 'a']);
    sortBy(block, 0);
    expect(ariaSorts(block)).toEqual(['none', 'none']);
    expect(cellsIn(block, 0)).toEqual(['b', 'a', 'c', 'd', 'e']);
  });

  it('starts a new column ascending and clears the old one', () => {
    const block = mount(tableHtml({ rows: rowsNamed(['b', 'a', 'c', 'd', 'e']) }));
    sortBy(block, 0);
    sortBy(block, 0);
    sortBy(block, 1);
    expect(ariaSorts(block)).toEqual(['none', 'ascending']);
  });

  it('orders numbers as numbers', () => {
    const block = mount(tableHtml({ rows: ['10', '9', '100', '2', '33'].map((qty, i) => tr(td('r' + i), td(qty))) }));
    sortBy(block, 1);
    expect(cellsIn(block, 1)).toEqual(['2', '9', '10', '33', '100']);
  });

  it('orders by data-sort over the visible text', () => {
    const rows = [
      ['three', 3],
      ['one', 1],
      ['two', 2],
      ['four', 4],
      ['five', 5]
    ];
    const block = mount(tableHtml({ rows: rows.map(([word, key]) => tr(td('x'), td(word, ` data-sort="${key}"`))) }));
    sortBy(block, 1);
    expect(cellsIn(block, 1)).toEqual(['one', 'two', 'three', 'four', 'five']);
  });

  it('orders text by locale with numeric runs', () => {
    const block = mount(tableHtml({ rows: rowsNamed(['banana', 'Apple', 'cherry', 'item10', 'item2']) }));
    sortBy(block, 0);
    expect(cellsIn(block, 0)).toEqual(['Apple', 'banana', 'cherry', 'item2', 'item10']);
  });

  it('sorts each tbody alone and keeps its group header first', () => {
    const block = mount(
      tableHtml({ bodies: groupBody('Group A', ['c', 'a']) + groupBody('Group B', ['b', 'e', 'd']) })
    );
    sortBy(block, 0);
    expect(bodyRows(block, 0)).toEqual(['Group A', 'a', 'c']);
    expect(bodyRows(block, 1)).toEqual(['Group B', 'b', 'd', 'e']);
    sortBy(block, 0);
    expect(bodyRows(block, 0)).toEqual(['Group A', 'c', 'a']);
    expect(bodyRows(block, 1)).toEqual(['Group B', 'e', 'd', 'b']);
  });
});

describe('filtering', () => {
  it('adds a filter only from eight rows', () => {
    expect(mount(tableHtml({ rows: rowsOf(7) })).querySelector('.vb-filter')).toBeNull();
    expect(mount(tableHtml({ rows: rowsOf(8) })).querySelector('.vb-filter')).not.toBeNull();
  });

  it('matches case-insensitively and reports n of N rows', () => {
    const block = mount(tableHtml({ rows: rowsOf(8) }));
    type(block.querySelector('.vb-filter'), '  ROW 3 ');
    expect(cellsIn(block, 0)).toEqual(['Row 3']);
    expect(block.querySelector('.vb-filter-status').textContent).toBe('1 of 8 rows');
  });

  it('clears the status and shows every row when the filter is emptied', () => {
    const block = mount(tableHtml({ rows: rowsOf(8) }));
    const input = block.querySelector('.vb-filter');
    type(input, 'row 3');
    type(input, '');
    expect(block.querySelector('.vb-filter-status').textContent).toBe('');
    expect(visibleRows(block)).toHaveLength(8);
  });

  it('reports 0 of N when nothing matches', () => {
    const block = mount(tableHtml({ rows: rowsOf(8) }));
    type(block.querySelector('.vb-filter'), 'nothing');
    expect(block.querySelector('.vb-filter-status').textContent).toBe('0 of 8 rows');
    expect(visibleRows(block)).toHaveLength(0);
  });

  it('hides a group header together with all its rows', () => {
    const block = mount(
      tableHtml({
        bodies:
          groupBody('Group A', ['Apple', 'Apricot', 'Avocado']) +
          groupBody('Group B', ['Banana', 'Blueberry', 'Blackberry', 'Boysenberry', 'Cherry'])
      })
    );
    const heads = Array.from(block.querySelectorAll('.vb-group-head'));
    const input = block.querySelector('.vb-filter');
    type(input, 'apr');
    expect(heads.map((head) => head.hidden)).toEqual([false, true]);
    type(input, 'blue');
    expect(heads.map((head) => head.hidden)).toEqual([true, false]);
  });
});

describe('row cap', () => {
  it('collapses 17 rows to 12 and adds no toggle at 16', () => {
    const long = mount(tableHtml({ rows: rowsOf(17) }));
    expect(visibleRows(long)).toHaveLength(12);
    expect(long.querySelector('.vb-more').hidden).toBe(false);
    const whole = mount(tableHtml({ rows: rowsOf(16) }));
    expect(visibleRows(whole)).toHaveLength(16);
    expect(whole.querySelector('.vb-more')).toBeNull();
  });

  it('toggles between all rows and the first 12, with aria-expanded', () => {
    const block = mount(tableHtml({ rows: rowsOf(17) }));
    const toggle = block.querySelector('.vb-more-toggle');
    expect(toggle.textContent).toBe('Show all 17 rows');
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    toggle.click();
    expect(visibleRows(block)).toHaveLength(17);
    expect(toggle.textContent).toBe('Show first 12 rows');
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    toggle.click();
    expect(visibleRows(block)).toHaveLength(12);
  });

  it('keeps the first 12 in the current sort order', () => {
    const block = mount(tableHtml({ rows: rowsOf(17) }));
    sortBy(block, 1);
    sortBy(block, 1);
    expect(cellsIn(block, 1)).toEqual(Array.from({ length: 12 }, (_, i) => String(17 - i)));
  });

  it('counts only the filter matches toward the cap', () => {
    const keep = Array.from({ length: 18 }, (_, i) => tr(td(`Keep ${i + 1}`), td('1')));
    const block = mount(tableHtml({ rows: [...keep, tr(td('Drop a'), td('0')), tr(td('Drop b'), td('0'))] }));
    const input = block.querySelector('.vb-filter');
    type(input, 'keep');
    expect(visibleRows(block)).toHaveLength(12);
    expect(block.querySelector('.vb-more-toggle').textContent).toBe('Show all 18 rows');
    type(input, 'drop');
    expect(visibleRows(block)).toHaveLength(2);
    expect(block.querySelector('.vb-more').hidden).toBe(true);
  });

  it('shows every row when printing, then restores the reader choice', () => {
    const block = mount(tableHtml({ rows: rowsOf(17) }));
    window.dispatchEvent(new Event('beforeprint'));
    expect(visibleRows(block)).toHaveLength(17);
    window.dispatchEvent(new Event('afterprint'));
    expect(visibleRows(block)).toHaveLength(12);
    block.querySelector('.vb-more-toggle').click();
    window.dispatchEvent(new Event('beforeprint'));
    window.dispatchEvent(new Event('afterprint'));
    expect(visibleRows(block)).toHaveLength(17);
  });
});
