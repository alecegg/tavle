# Proposal

## Why

The owner wants the components usable inside apps, not only in served or exported pages, fed the way A2UI renderers are fed (https://github.com/a2ui-project/a2ui) but drawn with Mithril instead of React, so one small ESM package can render agent-sent surfaces in any host page.

## What Changes

- An embeddable Mithril renderer (`<ui>/renderer`, ESM) that accepts A2UI v1.0 messages `createSurface`, `updateComponents`, `updateDataModel` and `deleteSurface`, reports renderer capabilities with `supportedCatalogIds`, resolves catalogs in A2UI order, maps `@accessibility` to ARIA, binds data with `{"@path": ...}` (two-way for inputs only) and reports answers as A2UI `action` messages.
- A Python producer in the library that turns ```ui text into those messages, attaching prepared draw props for the components whose drawing is computed in Python today.
- A standalone page builder that renders a message list into one self-contained HTML file through the same renderer.
- An ESM `exports` map in the library's `package.json` (renderer, views, generated component index, CSS, catalogs).
- Varde's served page gets a host adapter that maps the `answer` action to its existing POST.
- Deferred and listed in design.md: functions and function calls, local actions and other event actions, `@checks`, template child lists and relative scopes, two-way binding outside inputs, `sendDataModel`, inline catalogs, composition constraints, message validation in the browser, the A2UI conformance suite, converging varde pages onto the message renderer.

## Capabilities

### New Capabilities

- `ui-app-renderer`: the message set the renderer accepts, its capabilities, catalog resolution, data binding scope, prepared props, accessibility mapping, events to the host, and packaging.

### Modified Capabilities

(none)

## Impact

- Library (`~/source/<ui>`): new `static/renderer/` (import-free `index.js`, generated `entry.js`), `catalog/produce.py`, `catalog/surface_page.py`, generated `static/components/index.js` and `static/ui.css`, input schemas in the core catalog (`value`, `action`), `package.json` exports, tests.
- Varde: the answer host adapter in `src/varde/pages/static/` (task 4.4); served page output otherwise unchanged.
- Depends on `ui-catalogs` (catalog ids, names mapping, converter, `Stack`).
