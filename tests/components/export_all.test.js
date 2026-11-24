// The standalone export of a page holding every block type (test_export_standalone.py) mounts each
// host with no network and no server, including the hosts held inside the tabs and columns.
import { JSDOM, VirtualConsole } from 'jsdom';
import exported from './fixtures/export-callout.html?raw';

async function open() {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', (error) => errors.push(error.message));
  const dom = new JSDOM(exported, { runScripts: 'dangerously', virtualConsole });
  await new Promise((resolve) => dom.window.addEventListener('load', resolve));
  return { doc: dom.window.document, errors };
}

describe('standalone export of every block type', () => {
  // The tests only read the page, so one parse serves them all; parsing it per test timed out under load.
  let page;
  beforeAll(async () => {
    page = await open();
  });

  it('mounts every host and raises no script error', () => {
    const { doc, errors } = page;
    const hosts = [...doc.querySelectorAll('[data-mithril]')];
    expect(hosts.length).toBeGreaterThan(30);
    expect(hosts.filter((host) => host.dataset.mounted !== '1').map((host) => host.dataset.mithril)).toEqual([]);
    expect(errors).toEqual([]);
    expect(doc.querySelectorAll('script[src], link, iframe')).toHaveLength(0);
    expect([...doc.querySelectorAll('img')].filter((img) => !img.src.startsWith('data:'))).toHaveLength(0);
  });

  it('draws the containers and mounts the blocks they hold inside their panels', () => {
    const { doc } = page;
    const tabs = doc.querySelector('[data-mithril="tabs"] > section.vd-ctabs');
    expect(tabs.querySelectorAll(':scope > .vd-containers-panel').length).toBe(2);
    const held = tabs.querySelectorAll('.vd-containers-slot [data-mithril]');
    expect([...held].map((host) => host.dataset.mithril)).toEqual(['code', 'checklist']);
    expect([...held].every((host) => host.dataset.mounted === '1' && host.children.length > 0)).toBe(true);
    const columns = doc.querySelector('[data-mithril="columns"] > section.vd-columns');
    expect(columns.querySelectorAll('.vd-columns-panel .vd-containers-slot').length).toBeGreaterThan(1);
    // held blocks are the page's own nodes, so each shows once
    expect(doc.querySelectorAll('[data-mithril="code"][data-block-id="code"]').length).toBe(1);
  });

  it('disables the controls of every input block in a static export', () => {
    const { doc } = page;
    for (const name of ['choice', 'form', 'comment', 'ranking', 'slider']) {
      const controls = doc.querySelectorAll(`[data-mithril="${name}"] :is(button, input, select, textarea)`);
      expect(controls.length).toBeGreaterThan(0);
      expect([...controls].every((control) => control.disabled)).toBe(true);
    }
  });
});
