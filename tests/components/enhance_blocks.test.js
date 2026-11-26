import '@ui/static/blocks.js';

const enhancers = vi.hoisted(() => Array.from({ length: 13 }, () => vi.fn()));
vi.mock('@ui/static/table.js', () => ({ enhanceTables: enhancers[0] }));
vi.mock('@ui/static/tabs.js', () => ({ enhanceStates: enhancers[1] }));
vi.mock('@ui/static/flow.js', () => ({ enhanceFlow: enhancers[2] }));
vi.mock('@ui/static/chart.js', () => ({ enhanceChart: enhancers[3] }));
vi.mock('@ui/static/diagram.js', () => ({ enhanceDiagram: enhancers[4] }));
vi.mock('@ui/static/wireframe.js', () => ({ enhanceWireframe: enhancers[5] }));
vi.mock('@ui/static/code.js', () => ({ enhanceCode: enhancers[6] }));
vi.mock('@ui/static/annotated.js', () => ({ enhanceAnnotated: enhancers[7] }));
vi.mock('@ui/static/er.js', () => ({ enhanceEr: enhancers[8] }));
vi.mock('@ui/static/containers.js', () => ({ enhanceContainers: enhancers[9] }));
vi.mock('@ui/static/sequence.js', () => ({ enhanceSequence: enhancers[10] }));
vi.mock('@ui/static/image.js', () => ({ enhanceImage: enhancers[11] }));
vi.mock('@ui/static/screen_flow.js', () => ({ enhanceScreenFlow: enhancers[12] }));

function page() {
  document.body.innerHTML = '<main data-role="page"></main>';
  return document.querySelector('main');
}

function block(parent, ready = false) {
  const node = document.createElement('div');
  node.className = 'vb';
  if (ready) node.dataset.vbReady = '1';
  parent.append(node);
  return node;
}

function expectCalls(nodes) {
  for (const fn of enhancers) {
    expect(fn.mock.calls).toEqual(nodes.map((node) => [node]));
  }
}

afterEach(() => {
  document.body.replaceChildren();
  vi.clearAllMocks();
});

it('returns nothing when the page is missing', () => {
  expect(globalThis.tavlePageParts.blocks(document.body)).toBeUndefined();
  expectCalls([]);
});

it('enhances each unmarked block once, including mounted and added blocks', async () => {
  const main = page();
  const first = block(main);
  const second = block(main);
  const marked = block(main, true);
  const stop = globalThis.tavlePageParts.blocks(document.body);
  await vi.waitFor(() => expectCalls([first, second]));
  expect(first.dataset.vbReady).toBe('1');
  expect(second.dataset.vbReady).toBe('1');
  expect(marked.dataset.vbReady).toBe('1');

  const nested = block(first);
  main.dispatchEvent(new Event('vd-mounted'));
  await vi.waitFor(() => expectCalls([first, second, nested]));
  const added = block(main);
  await vi.waitFor(() => expectCalls([first, second, nested, added]));
  expect(added.dataset.vbReady).toBe('1');
  stop();
  const after = block(main);
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(after.hasAttribute('data-vb-ready')).toBe(false);
  expectCalls([first, second, nested, added]);
});

it('stops observing when stopped before imports resolve', async () => {
  const main = page();
  const observe = vi.spyOn(MutationObserver.prototype, 'observe');
  const stop = globalThis.tavlePageParts.blocks(document.body);
  stop();
  await vi.waitFor(() => expect(observe).toHaveBeenCalled());
  const after = block(main);
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(after.hasAttribute('data-vb-ready')).toBe(false);
  observe.mockRestore();
});
