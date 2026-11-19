// Data-model block, list and graph layouts. Props (blocks_render/backend.py, er.py): layout, summary,
// legend, copy and entities (name, change, was, fields of name/type/change/was/key); the list adds each
// entity's relations, the graph its drawing shapes, relations text and field foreign-key links.
function title(m, c, entity) {
  const { change, was } = entity;
  return [c.shared.changeName(m, entity.name, change, was), change ? [' ', c.shared.changeBadge(m, change, was)] : null];
}

function entityCard(m, c, entity) {
  const sh = c.shared;
  const table = sh.changeTable(m, ['field', 'type', m('span.vb-sr', 'flags')], sh.typedRows(m, entity.fields, true), `${entity.name} fields`);
  const relations = entity.relations.length
    ? m('ul.vb-relations', entity.relations.map((r) => m('li', ['→ ', m('strong', r.to), ' ', sh.badge(m, r.kind, 'vb-rel')])))
    : null;
  return sh.card(m, title(m, c, entity), [table, relations], entity.change ? `vd-change-card vd-change-${entity.change}` : '');
}

function listView(m, c, props) {
  return m('div.vb.data-model', { 'data-copy': props.copy }, [
    m('p.vb-alt', props.summary),
    m('div.vb-grid', props.entities.map((entity) => entityCard(m, c, entity))),
    props.legend ? m('p.vb-alt.vd-change-legend', props.legend) : null
  ]);
}

function fieldRows(m, c, props, entity) {
  const sh = c.shared;
  return entity.fields.map((f) => {
    let label = sh.changeName(m, f.name, f.change, f.was);
    if (f.fk) label = m('a.vd-er-fk', { href: `#vd-er-${props.digest}-${f.fk.target}` }, [label, ' → ', f.fk.name]);
    return { cells: [label, f.type, sh.keyCell(m, f.key)], change: f.change, was: f.was, label: f.name };
  });
}

function graphCard(m, c, props, entity) {
  const sh = c.shared;
  const table = sh.changeTable(m, ['field', 'type', m('span.vb-sr', 'flags')], fieldRows(m, c, props, entity), `${entity.name} fields`);
  const kind = entity.change ? `vd-change-card vd-change-${entity.change}` : '';
  return m('div.vd-er-card', { id: `vd-er-${props.digest}-${entity.index}`, 'data-entity': String(entity.index) },
    sh.card(m, title(m, c, entity), table, kind));
}

function graphView(m, c, props) {
  const d = props.drawing;
  const drawing = m('div.vd-er-view', {
    role: 'region',
    tabindex: '0',
    'aria-label': 'Entity relationship drawing; the relation list below has the same facts'
  }, m('svg.vd-er-svg', { viewBox: d.box, width: d.width, height: d.height, 'aria-hidden': 'true', focusable: 'false' }, c.shared.scene(m, d.shapes)));
  const relations = props.relations.length
    ? m('ul.vd-er-relations', { 'aria-label': 'Relations' }, props.relations.map((r) => m('li.vd-er-rel', { 'data-ends': r.ends }, r.text)))
    : m('p.vb-alt.vd-er-none', 'No relations.');
  return m('div.vb.data-model.vd-er', { 'data-copy': props.copy }, [
    m('p.vb-alt', props.summary),
    drawing,
    relations,
    m('div.vd-er-cards', props.entities.map((entity) => graphCard(m, c, props, entity))),
    props.legend ? m('p.vb-alt.vd-change-legend', props.legend) : null
  ]);
}

export function view(m, props, c) {
  return props.layout === 'graph' ? graphView(m, c, props) : listView(m, c, props);
}
