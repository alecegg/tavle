// Endpoint block. Props (blocks_render/backend.py): method, path, auth, change, was, note, request
// (rows of name/type/change/was, or null), responses (status/body/change/was), summary, legend, copy.
function responseRows(m, c, responses) {
  const rows = responses.map((r) => ({
    cells: [c.shared.badge(m, r.status, 'vb-status'), r.body],
    change: r.change,
    was: r.was,
    label: `response ${r.status}`
  }));
  return c.shared.changeTable(m, ['status', 'body'], rows, 'Responses');
}

export function view(m, props, c) {
  const { method, path, auth, change, was } = props;
  const sh = c.shared;
  const head = [
    sh.badge(m, method, 'vb-method'), ' ',
    sh.changeName(m, m('code', path), change, was, 'span'), ' ',
    sh.badge(m, `auth: ${auth}`, auth === 'none' ? 'vb-auth-none' : 'vb-auth'),
    change ? [' ', sh.changeBadge(m, change, was)] : null
  ];
  const parts = [
    props.note === null || props.note === undefined ? null : m('p', props.note),
    props.request ? sh.changeTable(m, ['request', 'type'], sh.typedRows(m, props.request, false), 'Request') : null,
    responseRows(m, c, props.responses)
  ];
  const kind = change ? `vd-change-card vd-change-${change}` : '';
  return m('div.vb.endpoint', { 'data-copy': props.copy }, [
    m('p.vb-alt', props.summary),
    sh.card(m, head, parts, kind),
    props.legend ? m('p.vb-alt.vd-change-legend', props.legend) : null
  ]);
}
