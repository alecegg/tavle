// Flow: a top-down diagram (props.view, drawn as shapes by the server) and the steps as text.
// Props: heading, alt ({summary, steps: {id, text, next}}) and, unless there are no steps,
// title, desc, unit, view (a diagram state) and copy. static/flow.js adds highlight and pan and zoom.
function step(m, s) {
  const names = s.next.flatMap((id, i) => (i ? [', ', m('code', id)] : [m('code', id)]));
  const branch = s.next.length > 1 ? [m('span.vb-badge.vb-branch', 'branch'), ' '] : null;
  return m('li.vb-step', { 'data-node': s.id }, [
    m('code.vb-step-id', s.id),
    ' ',
    m('span.vd-detail-text', s.text),
    s.next.length ? m('div.vb-next', [branch, 'then ', names]) : null
  ]);
}

function alternative(m, alt) {
  return m('details.vb-data', [m('summary', 'Steps as text'), m('p.vb-alt', alt.summary), m('ol.vb-flow', alt.steps.map((s) => step(m, s)))]);
}

export function view(m, props, c) {
  if (!props.view) return m('div.vb', c.shared.card(m, props.heading, alternative(m, props.alt)));
  const drawn = c.diagram.stateView(m, c, props.view, props.title, props.desc);
  const body = [m('div.vd-views', { 'data-min-unit': props.unit }, drawn), alternative(m, props.alt)];
  return m('div.vb.flow', { 'data-copy': props.copy }, c.shared.card(m, props.heading, body));
}
