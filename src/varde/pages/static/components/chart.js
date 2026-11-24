// Chart: an SVG the server drew (props.shapes), a legend, the events list and a data table.
// Props: heading, kind, title, desc, dense, box, shapes, legend ({n, class, marker, dash, name, key}),
// events ({n, label, kind, where, tone, class}), notes (text), table ({head, rows}), copy.
// static/chart.js adds the tooltip, readout, legend toggles and keyboard reading on the mounted DOM.
function legend(m, c, items) {
  if (items.length < 2) return null; // a single series is named by the title
  return m('ul.vb-legend', items.map((item) => m('li', {
    class: item.class,
    'data-series': String(item.n),
    'data-marker': item.marker,
    'data-dash': item.dash
  }, [
    m('svg.vb-key', { viewBox: '0 0 28 14', 'aria-hidden': 'true', focusable: 'false' }, c.shared.scene(m, item.key)),
    m('span.vb-name', item.name)
  ])));
}

function eventsList(m, events) {
  if (!events.length) return null;
  return [
    m('h5.vb-events-title', 'Events'),
    m('ol.vb-events', events.map((e) => m('li', {
      class: e.class,
      'data-event': String(e.n),
      'data-kind': e.kind,
      'data-where': e.where,
      'data-tone': e.tone
    }, [
      m('span.vb-ev-num', String(e.n)),
      m('span.vb-ev-label', e.label),
      ' ',
      m('span.vb-ev-meta', `(${e.kind}, ${e.where}, ${e.tone})`)
    ])))
  ];
}

function cellAttrs(series) {
  return series === null ? {} : { 'data-series': String(series) };
}

function grid(m, table) {
  const head = table.head.map(([text, series]) => m('th', cellAttrs(series), text));
  const rows = table.rows.map((row) => m('tr', cellAttrs(row.series === undefined ? null : row.series), [
    row.label === undefined ? null : m('th', { scope: 'row' }, row.label),
    row.cells.map(([text, series]) => m('td', cellAttrs(series), text))
  ]));
  return m('table.vb-data-grid', [m('thead', m('tr', head)), m('tbody', rows)]);
}

function eventsTable(m, c, events) {
  const head = ['Event', 'Kind', 'Where', 'Tone'].map((name) => m('th', name));
  const rows = events.map((e) => m('tr', [m('th', { scope: 'row' }, e.label), [e.kind, e.where, e.tone].map((text) => m('td', text))]));
  const table = m('table.vb-data-grid', [m('thead', m('tr', head)), m('tbody', rows)]);
  return [m('h5', 'Events'), c.shared.dataScroll(m, table, 'Events table')];
}

function notes(m, c, props) {
  if (props.events.length) return eventsTable(m, c, props.events);
  if (!props.notes.length) return null;
  return [m('h5', 'Notes'), m('ul.vb-notes', props.notes.map((text) => m('li', text)))];
}

function dataTable(m, c, props) {
  return m('details.vb-data', [
    m('summary', 'Data table'),
    m('p.vb-alt', props.desc),
    c.shared.dataScroll(m, grid(m, props.table), 'Data table'),
    notes(m, c, props)
  ]);
}

export function view(m, props, c) {
  const cls = `vb-chart${props.dense ? ' vb-dense' : ''}${props.kind === 'sparkline' ? ' vb-spark' : ''}`;
  const svg = c.shared.svgRoot(m, props.title, props.desc, props.box, cls, c.shared.scene(m, props.shapes));
  const plot = m('div.vb-plot', { 'data-kind': props.kind }, svg);
  const body = c.shared.card(m, props.heading, [plot, legend(m, c, props.legend), eventsList(m, props.events), dataTable(m, c, props)]);
  return m('div.vb.chart', { 'data-copy': props.copy }, body);
}
