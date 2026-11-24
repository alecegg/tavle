// The data-model (list and graph) and endpoint components' DOM equals the DOM of the former Python
// renderers, recorded in fixtures/<block>.json (props the server sends and the HTML it produced).
import { canonical, fragment } from './canonical.js';
import { loadComponents } from './registry.js';
import dataModel from './fixtures/data-model.json';
import endpoint from './fixtures/endpoint.json';

const { m, components } = loadComponents();

function render(block, props) {
  const host = document.createElement('div');
  m.render(host, components[block].view(m, props, components, undefined));
  return host;
}

for (const [block, cases] of Object.entries({ 'data-model': dataModel, endpoint })) {
  describe(`${block} block`, () => {
    it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
      expect(canonical(render(block, c.props))).toBe(canonical(fragment(c.html)));
    });
  });
}

describe('data-model graph hooks', () => {
  const graph = dataModel.find((c) => c.name === 'graph-basic').props;

  it('names each entity box, card and relation by index so er.js can highlight them', () => {
    const host = render('data-model', graph);
    expect([...host.querySelectorAll('svg [data-entity]')].map((n) => n.dataset.entity)).toEqual(['0', '1']);
    expect([...host.querySelectorAll('.vd-er-card')].map((n) => n.dataset.entity)).toEqual(['0', '1']);
    expect(host.querySelector('.vd-er-svg').getAttribute('aria-hidden')).toBe('true');
    expect(host.querySelectorAll('svg > g[data-ends]').length).toBe(graph.relations.length);
    expect(host.querySelector('.vd-er-fk').getAttribute('href')).toBe(`#${host.querySelectorAll('.vd-er-card')[1].id}`);
  });

  it('keeps hostile names as text', () => {
    const hostile = dataModel.find((c) => c.name === 'hostile').props;
    const host = render('data-model', hostile);
    expect(host.querySelector('img, script')).toBeNull();
    expect(host.textContent).toContain('<img src=x onerror=alert(1)>');
  });
});

describe('change vocabulary in data-model and endpoint', () => {
  const entity = (fields) => ({ layout: 'list', summary: '', legend: '', copy: null, entities: [{ name: 'a', change: '', was: '', relations: [], fields }] });
  const field = (extra) => ({ name: 'f', type: 'text', change: '', was: '', key: false, ...extra });

  it('shows a renamed field as old -> new with the word in the row name', () => {
    const host = render('data-model', entity([field({ change: 'renamed', was: 'name' })]));
    expect(host.querySelector('.vd-change-old').textContent).toBe('name');
    expect(host.querySelector('tbody tr').getAttribute('aria-label')).toBe('renamed f');
    expect(host.querySelector('.vd-change-badge').textContent).toContain('renamed');
  });

  it('keeps a removed field readable and marks every changed row', () => {
    const removed = render('data-model', entity([field({ change: 'removed' })]));
    expect(removed.querySelector('.vd-change-removed').textContent).toContain('removed');
    expect(removed.querySelector('td').textContent).toBe('f');
    const many = render('data-model', entity(Array.from({ length: 200 }, (_, i) => field({ name: `f${i}`, change: 'added' }))));
    expect(many.querySelectorAll('tr.vd-change-row').length).toBe(200);
    expect(many.querySelectorAll('.vd-change-badge').length).toBe(200);
  });

  it('shows a modified value with what it was, as text', () => {
    const host = render('data-model', entity([field({ change: 'modified', was: '<script>x</script>' })]));
    expect(host.querySelector('.vd-change-was').textContent).toBe('was <script>x</script>');
    expect(host.querySelector('script')).toBeNull();
  });
});
