// Canonical form of a DOM tree: tag, sorted attributes, adjacent text merged, empty text dropped.
// Mithril never creates empty text nodes, so two trees are equal when this form is.
export function canonical(node) {
  if (node.nodeType === 3) return JSON.stringify(node.data);
  const attrs = [...node.attributes].map((a) => `${a.name}=${JSON.stringify(a.value)}`).sort();
  const kids = [];
  for (const child of node.childNodes) {
    const last = kids.length - 1;
    if (child.nodeType === 3 && last >= 0 && kids[last].text !== undefined) kids[last].text += child.data;
    else kids.push(child.nodeType === 3 ? { text: child.data } : { node: child });
  }
  const inner = kids.filter((k) => k.text !== '').map((k) => (k.text !== undefined ? JSON.stringify(k.text) : canonical(k.node)));
  return `<${node.localName} ${attrs.join(' ')}>${inner.join('')}</${node.localName}>`;
}

export function fragment(html) {
  const root = document.createElement('div');
  root.innerHTML = html;
  return root;
}
