// Shared DOM helpers.
import {
  make,
  overlayParent,
  focusedIn,
  whileConnected,
  control,
  svgNode,
  keepInside,
  SVG_NS
} from '@ui/static/dom.js';
import { stubBox } from './stub-layout.js';

function shadowHost() {
  const host = document.createElement('div');
  document.body.append(host);
  return { host, shadow: host.attachShadow({ mode: 'open' }) };
}

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe('make', () => {
  it('sets only the tag when no class or text is given', () => {
    const node = make('p');
    expect(node.tagName).toBe('P');
    expect(node.hasAttribute('class')).toBe(false);
    expect(node.childNodes).toHaveLength(0);
  });

  it('sets the class and the text when given', () => {
    const node = make('span', 'vb-x', 'hello');
    expect(node.className).toBe('vb-x');
    expect(node.textContent).toBe('hello');
  });

  it('keeps an empty string as text and sets no class for an empty one', () => {
    const node = make('span', '', '');
    expect(node.hasAttribute('class')).toBe(false);
    expect(node.hasChildNodes()).toBe(false);
  });
});

describe('overlayParent', () => {
  it('returns the shadow root a node is inside', () => {
    const { shadow } = shadowHost();
    const inner = make('div');
    shadow.append(inner);
    expect(overlayParent(inner)).toBe(shadow);
  });

  it('returns the document body for a node in the document', () => {
    const node = make('div');
    document.body.append(node);
    expect(overlayParent(node)).toBe(document.body);
  });

  it('returns the document body for a detached node', () => {
    expect(overlayParent(make('div'))).toBe(document.body);
  });
});

describe('focusedIn', () => {
  it('returns the element focused in the same shadow tree', () => {
    const { shadow } = shadowHost();
    const button = make('button');
    const probe = make('div');
    shadow.append(button, probe);
    button.focus();
    expect(focusedIn(probe)).toBe(button);
  });

  it('returns the element focused in the document for a light-DOM node', () => {
    const button = make('button');
    const probe = make('div');
    document.body.append(button, probe);
    button.focus();
    expect(focusedIn(probe)).toBe(button);
  });

  it('returns null when the tree has nothing focused', () => {
    const { shadow } = shadowHost();
    const probe = make('div');
    shadow.append(probe);
    expect(focusedIn(probe)).toBeNull();
  });

  it('returns null for a light-DOM node when the document has nothing focused', () => {
    const probe = make('div');
    document.body.append(probe);
    document.activeElement.blur();
    expect(focusedIn(probe)).toBeNull();
  });

  it('returns null for a detached node', () => {
    expect(focusedIn(make('div'))).toBeNull();
  });
});

describe('whileConnected', () => {
  it('runs the handler on window events while the node is connected', () => {
    const node = make('div');
    document.body.append(node);
    const handler = vi.fn();
    whileConnected(node, 'dom-test-connected', handler);
    window.dispatchEvent(new Event('dom-test-connected'));
    window.dispatchEvent(new Event('dom-test-connected'));
    expect(handler).toHaveBeenCalledTimes(2);
  });

  it('skips the handler on the first event after the node is detached and removes itself', () => {
    const node = make('div');
    document.body.append(node);
    const handler = vi.fn();
    const removed = vi.spyOn(window, 'removeEventListener');
    whileConnected(node, 'dom-test-detached', handler);
    node.remove();
    window.dispatchEvent(new Event('dom-test-detached'));
    expect(handler).not.toHaveBeenCalled();
    expect(removed).toHaveBeenCalledWith('dom-test-detached', expect.any(Function));
  });
});

describe('control', () => {
  it('builds a button with the default class and no aria-label', () => {
    const node = control('Go', vi.fn());
    expect(node.tagName).toBe('BUTTON');
    expect(node.type).toBe('button');
    expect(node.className).toBe('vb-ctl');
    expect(node.textContent).toBe('Go');
    expect(node.hasAttribute('aria-label')).toBe(false);
  });

  it('uses the given class and aria-label when they are given', () => {
    const node = control('x', vi.fn(), 'vb-close', 'Close panel');
    expect(node.className).toBe('vb-close');
    expect(node.getAttribute('aria-label')).toBe('Close panel');
  });

  it('calls the click handler with the click', () => {
    const onClick = vi.fn();
    const node = control('Go', onClick);
    node.click();
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(onClick.mock.calls[0][0]).toBeInstanceOf(MouseEvent);
  });
});

describe('svgNode', () => {
  it('creates an element in the SVG namespace with the given attributes and class', () => {
    const node = svgNode('rect', { x: '1', width: '2' }, 'vd-box');
    expect(node.namespaceURI).toBe(SVG_NS);
    expect(node.localName).toBe('rect');
    expect(node.getAttribute('x')).toBe('1');
    expect(node.getAttribute('width')).toBe('2');
    expect(node.getAttribute('class')).toBe('vd-box');
  });

  it('sets no attributes or class when none are given', () => {
    const node = svgNode('g');
    expect(node.attributes).toHaveLength(0);
  });
});

describe('keepInside', () => {
  // The scrollport is 100 by 100 at the origin; with the default margin of 4 the usable area is 4 to 96.
  function setup(target) {
    const view = stubBox(make('div'), { width: 100, height: 100 });
    view.scrollLeft = 50;
    view.scrollTop = 30;
    stubBox(target.node, target.box);
    return view;
  }
  const targetAt = (box) => ({ node: make('span'), box });

  it('scrolls left by the exact overflow past the margin', () => {
    const target = targetAt({ left: -20, top: 40, width: 10, height: 10 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollLeft).toBe(50 - 24);
    expect(view.scrollTop).toBe(30);
  });

  it('scrolls right by the exact overflow past the margin', () => {
    const target = targetAt({ left: 90, top: 40, width: 20, height: 10 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollLeft).toBe(50 + 14);
  });

  it('scrolls up by the exact overflow past the margin', () => {
    const target = targetAt({ left: 40, top: -10, width: 10, height: 10 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollTop).toBe(30 - 14);
    expect(view.scrollLeft).toBe(50);
  });

  it('scrolls down by the exact overflow past the margin', () => {
    const target = targetAt({ left: 40, top: 90, width: 10, height: 20 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollTop).toBe(30 + 14);
  });

  it('leaves a target inside the margin where it is', () => {
    const target = targetAt({ left: 4, top: 4, width: 10, height: 10 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollLeft).toBe(50);
    expect(view.scrollTop).toBe(30);
  });

  it('uses the margin option as the edge', () => {
    const target = targetAt({ left: 5, top: 40, width: 10, height: 10 });
    const view = setup(target);
    keepInside(view, target.node, { margin: 10 });
    expect(view.scrollLeft).toBe(50 - 5);
  });

  it('reserves insetTop above the target for a sticky header', () => {
    const target = targetAt({ left: 40, top: 10, width: 10, height: 10 });
    const view = setup(target);
    keepInside(view, target.node, { insetTop: 20 });
    expect(view.scrollTop).toBe(30 - 14);
  });

  it('makes no horizontal move for a target wider than the view', () => {
    const target = targetAt({ left: -20, top: 40, width: 150, height: 10 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollLeft).toBe(50);
  });

  it('makes no vertical move when vertical is false', () => {
    const target = targetAt({ left: 40, top: -10, width: 10, height: 10 });
    const view = setup(target);
    keepInside(view, target.node, { vertical: false });
    expect(view.scrollTop).toBe(30);
  });

  it('makes no vertical move for a target taller than the view', () => {
    const target = targetAt({ left: 40, top: -10, width: 10, height: 100 });
    const view = setup(target);
    keepInside(view, target.node);
    expect(view.scrollTop).toBe(30);
  });
});
