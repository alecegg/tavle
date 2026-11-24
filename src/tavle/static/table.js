// table and data-model: sort, filter, row cap, scroll hint and edge fades, relations.
import { make, control, keepInside, whileConnected } from './dom.js';

// A short table is read at a glance: filter and sort controls appear only from these row counts.
const MIN_ROWS_FOR_FILTER = 8;
const MIN_ROWS_FOR_SORT = 5;
// A longer table shows this many rows and a toggle that names the total; a scroll region would cut a row in half.
const COLLAPSED_ROWS = 12;
// A table collapses only when the toggle would hide at least this many rows: hiding two or three
// rows behind a button costs the reader more than it saves.
const MIN_HIDDEN_ROWS = 5;

function collapses(matched) {
  return matched - COLLAPSED_ROWS >= MIN_HIDDEN_ROWS;
}

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

// Maps each data row to whether it matches the filter text.
function matchingRows(table, needle) {
  const hits = new Map();
  for (const body of table.tBodies) {
    for (const row of dataRows(body)) {
      hits.set(row, !needle || row.textContent.toLowerCase().includes(needle));
    }
  }
  return hits;
}

// Shows the rows that match the filter, in their current order, up to the cap when the table
// collapses and is not expanded. Returns the match count; the group header of a body with nothing
// shown hides.
function showRows(table, state) {
  const hits = matchingRows(table, state.needle);
  const matched = Array.from(hits.values()).filter(Boolean).length;
  const capped = !state.expanded && collapses(matched);
  showMatchingBodies(table, hits, capped);
  if (state.more) updateMore(state, matched);
  return matched;
}

function showMatchingBodies(table, hits, capped) {
  let shown = 0;
  for (const body of table.tBodies) {
    const rows = dataRows(body);
    for (const row of rows) {
      if (hits.get(row)) shown += 1;
      row.hidden = !hits.get(row) || (capped && shown > COLLAPSED_ROWS);
    }
    const head = body.querySelector('.vb-group-head');
    if (head) head.hidden = rows.every((row) => row.hidden);
  }
}

function updateMore(state, matched) {
  const button = state.more.firstElementChild;
  state.more.hidden = !collapses(matched);
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

// The scroll hint shows only while the table is wider than its region; each edge with columns past it fades.
function trackOverflow(region, hint) {
  const update = () => {
    const overflowing = region.scrollWidth > region.clientWidth + 1;
    const start = Math.abs(region.scrollLeft);
    hint.hidden = !overflowing;
    region.classList.toggle('vb-more-start', overflowing && start > 1);
    region.classList.toggle('vb-more-end', overflowing && start + region.clientWidth < region.scrollWidth - 1);
  };
  update();
  whileConnected(region, 'resize', update);
  region.addEventListener('click', update);
  region.addEventListener('scroll', update, { passive: true });
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
  if (total >= MIN_ROWS_FOR_FILTER) bar.append(...filterField(table, state, total));
  if (state.sortable && table.classList.contains('vb-table-stack')) bar.append(sortPicker(table, state));
  bar.append(hint);
  trackOverflow(region, hint);
  region.after(bar);
  if (collapses(total)) region.after(moreToggle(table, state));
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
