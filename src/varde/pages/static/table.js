// table and data-model: sort, filter, row cap, wrap toggle, scroll hint, relations.
import { make, control, keepInside, whileConnected } from './dom.js';

// A short table is read at a glance: filter and sort controls appear only from these row counts.
const MIN_ROWS_FOR_FILTER = 8;
const MIN_ROWS_FOR_SORT = 5;
// A longer table shows this many rows and a toggle that names the total; a scroll region would cut a row in half.
const COLLAPSED_ROWS = 12;

function cellValue(row, column) {
  const cell = row.cells[column];
  if (!cell) return '';
  return cell.textContent.trim();
}

function compareCells(a, b) {
  const na = Number(a);
  const nb = Number(b);
  if (a !== '' && b !== '' && !Number.isNaN(na) && !Number.isNaN(nb)) return na - nb;
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
}

function dataRows(body) {
  return Array.from(body.rows).filter((row) => !row.classList.contains('vb-group-head'));
}

// Rows sort inside their own tbody, so a group keeps its header and its rows.
// direction: 1 ascending, -1 descending, 0 as authored.
function applySort(table, state, column, direction) {
  state.direction = direction;
  state.column = direction === 0 ? -1 : column;
  for (const body of table.tBodies) {
    const head = Array.from(body.rows).filter((row) => row.classList.contains('vb-group-head'));
    const rows = state.original.get(body).slice();
    if (direction !== 0) {
      rows.sort((x, y) => direction * compareCells(cellValue(x, column), cellValue(y, column)));
    }
    body.replaceChildren(...head, ...rows);
  }
  table.tHead.querySelectorAll('th').forEach((th, index) => {
    const active = direction !== 0 && index === column;
    th.setAttribute('aria-sort', active ? (direction === 1 ? 'ascending' : 'descending') : 'none');
  });
  if (state.picker) state.picker.value = direction === 0 ? '' : column + ':' + direction;
  showRows(table, state);
}

function cycleSort(table, state, column) {
  const direction = state.column === column ? (state.direction + 2) % 3 - 1 : 1;
  applySort(table, state, column, direction);
}

function tableState(table, sortable) {
  const original = new Map(Array.from(table.tBodies, (body) => [body, dataRows(body)]));
  return { column: -1, direction: 0, original, picker: null, needle: '', expanded: false, more: null, sortable };
}

function addSortButtons(table, state) {
  table.tHead.querySelectorAll('th').forEach((th, index) => {
    if (!th.textContent.trim()) return;
    const button = make('button', 'vb-sort');
    button.type = 'button';
    button.append(...th.childNodes);
    button.addEventListener('click', () => cycleSort(table, state, index));
    th.append(button);
    th.setAttribute('aria-sort', 'none');
  });
}

// Stack mode hides the header (and its buttons), so phones sort through a select.
function sortPicker(table, state) {
  const label = make('label', 'vb-sortpick');
  const select = make('select', 'vb-sortselect');
  select.append(new Option('As authored', ''));
  table.tHead.querySelectorAll('th').forEach((th, index) => {
    const name = th.textContent.trim();
    if (!name) return;
    select.append(new Option(name + ', ascending', index + ':1'));
    select.append(new Option(name + ', descending', index + ':-1'));
  });
  select.addEventListener('change', () => {
    const [column, direction] = select.value ? select.value.split(':').map(Number) : [-1, 0];
    applySort(table, state, column, direction);
  });
  state.picker = select;
  label.append('Sort by ', select);
  return label;
}

// Shows the rows that match the filter, in their current order, up to the cap unless expanded.
// Returns the match count; the group header of a body with nothing shown hides.
function showRows(table, state) {
  let matched = 0;
  for (const body of table.tBodies) {
    let visible = 0;
    for (const row of dataRows(body)) {
      const hit = !state.needle || row.textContent.toLowerCase().includes(state.needle);
      if (hit) matched += 1;
      row.hidden = !hit || (!state.expanded && matched > COLLAPSED_ROWS);
      if (!row.hidden) visible += 1;
    }
    const head = body.querySelector('.vb-group-head');
    if (head) head.hidden = visible === 0;
  }
  if (state.more) updateMore(state, matched);
  return matched;
}

function updateMore(state, matched) {
  const button = state.more.firstElementChild;
  state.more.hidden = matched <= COLLAPSED_ROWS;
  button.textContent = state.expanded ? 'Show first ' + COLLAPSED_ROWS + ' rows' : 'Show all ' + matched + ' rows';
  button.setAttribute('aria-expanded', String(state.expanded));
}

function moreToggle(table, state) {
  const wrap = make('div', 'vb-more');
  wrap.append(control('', () => {
    state.expanded = !state.expanded;
    showRows(table, state);
  }, 'vb-ctl vb-more-toggle'));
  state.more = wrap;
  // Print every row: a printed page has no toggle to press.
  let wasExpanded = false;
  window.addEventListener('beforeprint', () => {
    wasExpanded = state.expanded;
    state.expanded = true;
    showRows(table, state);
  });
  window.addEventListener('afterprint', () => {
    state.expanded = wasExpanded;
    showRows(table, state);
  });
  return wrap;
}

function filterField(table, state, total) {
  const input = make('input', 'vb-filter');
  input.type = 'search';
  input.placeholder = 'Filter rows';
  input.setAttribute('aria-label', 'Filter rows');
  const status = make('span', 'vb-filter-status');
  status.setAttribute('aria-live', 'polite');
  input.addEventListener('input', () => {
    state.needle = input.value.trim().toLowerCase();
    const matched = showRows(table, state);
    status.textContent = state.needle ? matched + ' of ' + total + ' rows' : '';
  });
  return [input, status];
}

function wrapToggle(region) {
  const button = control('Wrap text', () => {
    const wrapped = region.classList.toggle('vb-nowrap');
    button.setAttribute('aria-pressed', String(!wrapped));
  }, 'vb-ctl vb-wrap-toggle');
  button.setAttribute('aria-pressed', 'true');
  return button;
}

// The scroll hint and the wrap toggle show only while the table is wider than its region;
// the toggle also stays while text is unwrapped, so the reader can wrap it again.
function trackOverflow(region, hint, toggle) {
  const update = () => {
    const overflowing = region.scrollWidth > region.clientWidth + 1;
    hint.hidden = !overflowing;
    toggle.hidden = !overflowing && !region.classList.contains('vb-nowrap');
  };
  update();
  whileConnected(region, 'resize', update);
  region.addEventListener('click', update);
  toggle.addEventListener('click', update);
  if (typeof ResizeObserver === 'function') new ResizeObserver(update).observe(region);
}

// Chromium does not scroll sideways to a focused control in a sticky first column, so do it here.
function keepFocusVisible(region) {
  region.addEventListener('focusin', (event) => {
    if (event.target !== region) keepInside(region, event.target, { vertical: false });
  });
}

function rowCount(table) {
  return Array.from(table.tBodies).reduce((sum, body) => sum + dataRows(body).length, 0);
}

function addToolbar(table, state, total) {
  const region = table.closest('.vb-scroll');
  if (!region) return;
  keepFocusVisible(region);
  const bar = make('div', 'vb-filterbar');
  const hint = make('span', 'vb-scrollhint', 'Scrolls sideways');
  const toggle = wrapToggle(region);
  if (total >= MIN_ROWS_FOR_FILTER) bar.append(...filterField(table, state, total));
  if (state.sortable && table.classList.contains('vb-table-stack')) bar.append(sortPicker(table, state));
  bar.append(toggle, hint);
  trackOverflow(region, hint, toggle);
  region.after(bar);
  if (total > COLLAPSED_ROWS) region.after(moreToggle(table, state));
  showRows(table, state);
}

function collapseRelations(list) {
  const count = list.children.length;
  const button = control('Relations (' + count + ')', () => {
    list.hidden = !list.hidden;
    button.setAttribute('aria-expanded', String(!list.hidden));
  }, 'vb-ctl vb-toggle');
  button.setAttribute('aria-expanded', 'true');
  list.before(button);
}

export function enhanceTables(block) {
  for (const table of block.querySelectorAll('table.vb-table')) {
    if (!table.tHead || !table.tBodies[0]) continue;
    const total = rowCount(table);
    const state = tableState(table, total >= MIN_ROWS_FOR_SORT);
    if (state.sortable) addSortButtons(table, state);
    addToolbar(table, state, total);
  }
  for (const list of block.querySelectorAll('.vb-relations')) collapseRelations(list);
}
