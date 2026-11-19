// Each input block's component DOM equals the DOM of the former Python renderer, recorded in
// fixtures/<block>.json (inputs, the props the server sends, the id and the HTML it produced).
// `data-props` is compared as JSON: Python and JavaScript space their JSON differently.
import { canonical, fragment } from './canonical.js';
import { mountComponents } from '@varde/pages-static/components/mount.js';
import { loadComponents } from './registry.js';
import choice from './fixtures/choice.json';
import form from './fixtures/form.json';
import comment from './fixtures/comment.json';
import ranking from './fixtures/ranking.json';
import slider from './fixtures/slider.json';

const blocks = { choice, form, comment, ranking, slider };
const { m, components } = loadComponents();

function normalizeProps(root) {
  for (const el of root.querySelectorAll('[data-props]')) {
    el.setAttribute('data-props', JSON.stringify(JSON.parse(el.getAttribute('data-props'))));
  }
  return root;
}

function mount(block, props, id) {
  const host = document.createElement('div');
  m.render(host, components[block].view(m, props, components, id));
  return host;
}

for (const [block, cases] of Object.entries(blocks)) {
  describe(`${block} block`, () => {
    it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
      const host = normalizeProps(mount(block, c.props, c.id ?? undefined));
      expect(canonical(host)).toBe(canonical(normalizeProps(fragment(c.html))));
    });
  });
}

describe('mounting keeps what the reader entered', () => {
  const field = { name: 'owner', label: 'Owner', type: 'text', required: true, hint: '', limit: 600, client: { name: 'owner', type: 'text', required: true } };

  it('a second boot pass over mounted hosts leaves values and focus alone', () => {
    const page = document.createElement('main');
    document.body.append(page);
    const props = { title: '', submit: 'Submit', fields: [field] };
    page.innerHTML = `<div data-mithril="form" data-block-id="f"><script type="application/json">${JSON.stringify(props)}</script></div>`;
    const run = () => mountComponents(page, m, components);
    expect(run()).toBe(1);
    const input = page.querySelector('[data-field="owner"]');
    input.value = 'typed';
    input.focus();
    expect(run()).toBe(0); // the MutationObserver in the bundle fires this on every live update
    expect(page.querySelector('[data-field="owner"]')).toBe(input);
    expect(input.value).toBe('typed');
    expect(document.activeElement).toBe(input);
    page.remove();
  });

  it('read-only hosts disable every control once mounted', () => {
    const page = document.createElement('main');
    document.body.append(page);
    const props = { question: 'Q', items: [{ label: 'a', value: 'a', detail: '', name: 'a' }, { label: 'b', value: 'b', detail: '', name: 'b' }] };
    page.innerHTML = `<div data-readonly data-mithril="ranking" data-block-id="r"><script type="application/json">${JSON.stringify(props)}</script></div>`;
    mountComponents(page, m, components);
    const buttons = [...page.querySelectorAll('button')];
    expect(buttons.length).toBe(5);
    expect(buttons.every((button) => button.disabled)).toBe(true);
    page.remove();
  });

  it('a host with no id draws the same markup as the Python renderer did (None)', () => {
    const host = mount('comment', { label: 'L', submit: 'Send', maxNote: 8000 }, undefined);
    expect(host.querySelector('.comment-item').dataset.item).toBe('None');
  });
});
