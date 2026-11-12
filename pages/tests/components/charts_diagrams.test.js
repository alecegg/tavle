// Each chart and diagram block's component DOM equals the DOM of the former Python renderer,
// recorded in fixtures/<block>.json (inputs, the props the server sends, and the HTML it produced).
import { canonical, fragment } from './canonical.js';
import { loadComponents } from './registry.js';
import chart from './fixtures/chart.json';
import diagram from './fixtures/diagram.json';
import flow from './fixtures/flow.json';
import state from './fixtures/state.json';
import sequence from './fixtures/sequence.json';
import wireframe from './fixtures/wireframe.json';
import uiStates from './fixtures/ui-states.json';
import screenFlow from './fixtures/screen-flow.json';
import image from './fixtures/image.json';

const blocks = { chart, diagram, flow, state, sequence, wireframe, 'ui-states': uiStates, 'screen-flow': screenFlow, image };
const { m, components } = loadComponents();

for (const [block, cases] of Object.entries(blocks)) {
  describe(`${block} block`, () => {
    it.each(cases.map((c) => [c.name, c]))('component DOM equals the Python DOM: %s', (_name, c) => {
      const host = document.createElement('div');
      m.render(host, components[block].view(m, c.props, components, undefined));
      expect(canonical(host)).toBe(canonical(fragment(c.html)));
    });
  });
}
