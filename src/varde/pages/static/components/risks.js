// Risks block as a component: a 3x3 likelihood-by-impact grid and the full risk list.
const LEVELS = ['low', 'medium', 'high'];
const SCORE = { low: 1, medium: 2, high: 3 };
const SEVERITIES = ['low', 'medium', 'high', 'critical'];
const ICONS = { low: 'ring', medium: 'half', high: 'triangle', critical: 'diamond' };
const WORDS = { low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' };
const CHIPS_PER_CELL = 4;
const OPTIONAL = ['mitigation', 'owner'];

// Likelihood x impact (1 to 9): 1-2 low, 3-4 medium, 6 high, 9 critical.
function severityOf(likelihood, impact) {
  const score = SCORE[likelihood] * SCORE[impact];
  if (score <= 2) return 'low';
  if (score <= 4) return 'medium';
  return score <= 6 ? 'high' : 'critical';
}

function severity(risk) {
  return severityOf(risk.likelihood, risk.impact);
}

// `4 risks: 1 critical, 2 high, 1 low`; counts of zero are left out.
function summaryText(c, risks) {
  const parts = [...SEVERITIES]
    .reverse()
    .map((s) => [risks.filter((r) => severity(r) === s).length, s])
    .filter(([n]) => n)
    .map(([n, s]) => `${n} ${s}`);
  return `${c.shared.countNoun(risks.length, 'risk', 'risks')}: ${parts.join(', ')}`;
}

function copyText(risks) {
  return risks
    .map((r) => {
      const head = `${r.id}: ${r.label} (likelihood ${r.likelihood}, impact ${r.impact}, severity ${severity(r)})`;
      return head + OPTIONAL.map((key) => (key in r ? `; ${key}: ${r[key]}` : '')).join('');
    })
    .join('\n');
}

function cell(m, c, likelihood, impact, risks) {
  const sev = severityOf(likelihood, impact);
  const here = risks.filter((r) => r.likelihood === likelihood && r.impact === impact);
  const extra = here.length - CHIPS_PER_CELL;
  return m(`div.vd-risk-cell.vd-risk-cell-${sev}${here.length ? '' : '.vd-risk-empty'}`, [
    c.icons.icon(m, ICONS[sev], 'vd-risk-glyph'),
    here.slice(0, CHIPS_PER_CELL).map((r) => m('span.vd-risk-chip', r.id)),
    extra > 0 ? m('span.vd-risk-more', `+${extra}`) : null
  ]);
}

function grid(m, c, risks) {
  return m('div.vd-risk-grid', { role: 'img', 'aria-label': summaryText(c, risks) }, [
    m('span.vd-risk-corner'),
    LEVELS.map((level) => m('span.vd-risk-colhead', WORDS[level])),
    [...LEVELS].reverse().map((likelihood) => [
      m('span.vd-risk-rowhead', WORDS[likelihood]),
      LEVELS.map((impact) => cell(m, c, likelihood, impact, risks))
    ])
  ]);
}

function field(m, key, value) {
  return m('dd', [m('span.vd-risk-key', key), ' ', value]);
}

function entry(m, c, risk) {
  const sev = severity(risk);
  return m(`div.vd-risk-entry.vd-risk-sev-${sev}`, [
    m('dt', [m('span.vd-risk-id', risk.id), ' ', m('span.vd-risk-label', risk.label)]),
    field(m, 'Likelihood', WORDS[risk.likelihood]),
    field(m, 'Impact', WORDS[risk.impact]),
    field(m, 'Severity', [c.icons.icon(m, ICONS[sev], 'vd-risk-sevmark'), ' ', m('span.vd-risk-sevword', WORDS[sev])]),
    OPTIONAL.filter((key) => key in risk).map((key) => field(m, key[0].toUpperCase() + key.slice(1), String(risk[key])))
  ]);
}

export function view(m, props, c) {
  const risks = c.shared.objects(props.item);
  const title = props.title || 'Risks';
  return m('section.vb.risks.vd-risk', { 'aria-label': title, 'data-copy': copyText(risks) }, [
    props.title ? m('p.vd-risk-title', props.title) : null,
    m('p.vb-alt.vd-risk-summary', summaryText(c, risks)),
    m('p.vd-risk-axes', 'Rows are likelihood, high at the top. Columns are impact, low at the left.'),
    grid(m, c, risks),
    m('dl.vd-risk-list', risks.map((risk) => entry(m, c, risk)))
  ]);
}
