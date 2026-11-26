// jsdom has no layout: give one element the box a test needs. Only that element changes.
// Later tests read the same numbers through getBoundingClientRect and the client* properties.
export function stubBox(node, { left = 0, top = 0, width = 0, height = 0, clientLeft = 0, clientTop = 0 } = {}) {
  Object.defineProperties(node, {
    getBoundingClientRect: {
      configurable: true,
      value: () => ({ x: left, y: top, left, top, width, height, right: left + width, bottom: top + height })
    },
    clientWidth: { configurable: true, value: width },
    clientHeight: { configurable: true, value: height },
    clientLeft: { configurable: true, value: clientLeft },
    clientTop: { configurable: true, value: clientTop }
  });
  return node;
}
