// File tree: folders as <details>, files with change badges. Props: title, summary, copy, collapse
// (folders deeper than this start closed; null opens all), folders and files (the folded, ordered
// tree: single-child chains already joined), links (path -> id of the code block showing that file).
const MAX_INDENT_LEVEL = 5; // folders nested deeper than this stop indenting

function fileItem(m, c, links, file) {
  const change = file.change;
  const target = links[file.path];
  const leaf = target
    ? m('a.vd-file-tree-link', { href: `#${target}` }, file.name)
    : m('span.vd-file-tree-leaf', file.name);
  const klass = `vd-file-tree-file${change ? ` vd-change-row vd-change-${change}` : ''}`;
  return m('li', { class: klass, role: 'treeitem', 'aria-label': file.label },
    m('span.vd-file-tree-row', [
      change ? [c.shared.changeBadge(m, change, ''), ' '] : null,
      c.shared.changeName(m, leaf, change, file.was),
      file.role ? [' ', m('span.vd-file-tree-role', file.role)] : null,
      file.note ? [' ', m('span.vd-file-tree-note', file.note)] : null
    ]));
}

function folderItem(m, c, props, folder, depth) {
  const noun = folder.count === 1 ? 'file' : 'files';
  const isOpen = props.collapse === null || props.collapse === undefined || depth <= props.collapse;
  return m('li.vd-file-tree-folder', { role: 'treeitem' },
    m('details', { open: isOpen }, [
      m('summary.vd-file-tree-sum', { 'aria-label': `folder ${folder.path}, ${folder.count} ${noun}` }, [
        m('span.vd-file-tree-dir', `${folder.name}/`),
        ' ',
        m('span.vd-file-tree-count', `${folder.count} ${noun}`)
      ]),
      list(m, c, props, folder, depth + 1, '')
    ]));
}

function list(m, c, props, node, depth, label) {
  const attrs = { class: `vd-file-tree-list${depth > MAX_INDENT_LEVEL ? ' vd-file-tree-flat' : ''}` };
  if (label) {
    attrs.role = 'tree';
    attrs['aria-label'] = label;
  } else {
    attrs.role = 'group';
  }
  const links = props.links || {};
  return m('ul', attrs, [
    node.folders.map((folder) => folderItem(m, c, props, folder, depth)),
    node.files.map((file) => fileItem(m, c, links, file))
  ]);
}

export function view(m, props, c) {
  return m('div.vb.file-tree.vd-file-tree', { 'data-copy': props.copy }, [
    props.title ? m('p.vd-file-tree-title', props.title) : null,
    m('p.vb-alt.vd-file-tree-summary', props.summary),
    list(m, c, props, props, 1, props.title || 'Changed files')
  ]);
}
