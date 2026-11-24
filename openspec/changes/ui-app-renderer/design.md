# Design

## Context

Owner direction (settled 2026-11-24, lead's brief): "the general idea https://github.com/a2ui-project/a2ui is the same as what we want here but ... package items in mithril js instead of a full react allowing for easily creating individual servable html pages in addition to app use"; the app renderer accepts A2UI-style messages (`createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface`, renderer capabilities with `supportedCatalogIds`).

A2UI sources read (`~/source/reference-repos/a2ui` at `a337e800`):

- `specification/v1_0/json/agent_to_renderer.json` `$defs`: `CreateSurfaceMessage` (`surfaceId` required; optional `catalogId`, `components`, `dataModel`, `sendDataModel`, `metadata`), `UpdateComponentsMessage` (`surfaceId`, `components`), `UpdateDataModelMessage` (`surfaceId`, optional `path`, `value`; `null` deletes), `DeleteSurfaceMessage`, `CallRendererFunctionMessage`, `AgentFunctionResponseMessage`; every message carries `version: "1.0"`.
- `specification/v1_0/json/renderer_capabilities.json`: `{"1.0": {"supportedCatalogIds": [...], "inlineCatalogs": [...]}}`.
- `specification/v1_0/docs/a2ui_protocol.md:493-560`: component envelope (`id`, `component`, `@catalogId`, `@accessibility`, `@metadata`, `@checks`), catalog resolution order with no fallback, accessibility requirements (plumb `label`, `description`, `live`, `hidden` to ARIA; explicit values override inferred ones); `:779-810`: adjacency list, exactly one `root`, updates buffered until `root` exists, invalid references skipped; `:907-1030`: data binding, scopes, two-way binding (`:986` "Two-way binding & input components"). The v1.0 binding object is `{"@path": "/x"}` (`specification/v1_0/json/common_types.json` `$defs.DataBinding`: one required key `@path`, `additionalProperties: false`).
- `specification/v1_0/json/common_types.json` `$defs.Action`: `oneOf` `{event: {name, userMessage?, context?}}` (agent-side event; `context` values are literals or bindings) or `{functionCall}` (local function). `specification/v1_0/json/renderer_to_agent.json`: the renderer's `{version: "1.0", action: {name, surfaceId, sourceComponentId, timestamp, context, metadata?}}` message, `context` with bindings resolved.
- `typescript/core/web_core` and `typescript/renderers/{lit,react,angular}`: framework renderers over a shared message processor; this change writes its own small processor in plain JS instead of depending on `web_core` (the library keeps no runtime dependencies besides Mithril, which the host passes in).

Library facts: views are `view(m, props, components, blockId, held)` (`static/components/mount.js`), enhancers wire themselves on the bubbling `vd-mounted` event, 24 components draw from props prepared in Python (`blocks_render/registry.py` `_PROPS`), input components report answers through the host port `ctx.answer` (ui-extract D1).

## Goals / Non-Goals

**Goals:** a renderer a host page can import, feed A2UI messages and get the same drawing as a varde page; a Python producer for those messages; a standalone page from a message list.

**Non-Goals:** the deferred list in R6; a transport (the host delivers messages); porting the Python layout to JS (ui-extract Q2).

## Decisions

### R1. Message set

`createRenderer({ m, root, catalogs, enhancers, onEvent })` returns `{ capabilities(), process(message), surfaces() }`. Every dependency arrives as a parameter (R7): Mithril as `m`, views inside `catalogs`, enhancer install functions as `enhancers`.

- `createSurface`: creates a surface element under `root`; error if the id exists. Inline `components` and `dataModel` are applied as if sent in the following messages.
- `updateComponents`: merges components into the surface's map by `id` (replace whole component); renders once `root` exists; buffers until then; a reference to a missing id draws nothing for that slot and reports a `missing-component` event.
- `updateDataModel`: sets the value at `path` (JSON Pointer, default `/` replaces the model; `null` deletes the key) and re-renders the surface.
- `deleteSurface`: removes the element and its state.
- Anything else (including `callRendererFunction`) or a `version` other than `"1.0"`: an `unsupported-message` event, no state change.

Errors never throw out of `process`; they go to `onEvent({type, surfaceId, componentId, message})`. User actions go to the same `onEvent` as A2UI action messages (R5), told apart by their `action` key.

### R2. Capabilities and catalog resolution

`capabilities()` returns `{"1.0": {"supportedCatalogIds": [<core id>, ...ids of the catalogs passed in]}}`. A catalog entry passed to `createRenderer` is `{ catalogId, components: { <Name>: view module } , prepared: Set<Name> }`, built for core by the generated index (R7). Resolution follows A2UI: the component's `@catalogId`, else the surface `catalogId`, else an `unresolved-catalog` event; no fallback.

### R3. Prepared props

For a component whose catalog entry has `<ui>_prepare: "python"`, the view needs draw props. The Python producer (`catalog/produce.py`, `surface_messages(ui_text, surface_id, prepared=True)`) runs the props hooks and puts the result in `@metadata.extensions.<ui>_drawn` (a schema-valid place: `common_types.json#/$defs/Extensions`). The renderer draws `<ui>_drawn` when present, the component's own props for components with no prepare step, and otherwise an error card "needs prepared props" plus a `needs-prepare` event. A producer that is not the library can therefore use every component without a prepare step today (`Callout`, `Checklist`, `Stats`, `Timeline`, `Table`, `Matrix`, `Risks`, `Recap`, `Stack`, `Decision`, custom components ...) and the rest through the Python producer. Alternative rejected for now: port the hooks to JS (ui-extract Q2, about 6,400 lines).

### R4. Data binding scope

A property value `{"@path": "/abs/pointer"}` (A2UI v1.0 `DataBinding`) is replaced by the model value at render time for components with no prepare step. Relative paths, collection scopes, template child lists and `formatString` are not supported: such a value draws the error card and reports `unsupported-binding`. A binding inside a prepared component is refused the same way (the drawn props would not follow the model), except the input binding below.

Two-way binding for inputs only: an input component's `value: {"@path": "/answers/<id>"}` is read at render and written locally when the user changes the control (A2UI two-way binding, `a2ui_protocol.md:986`); the write updates the model and re-renders, and sends nothing to the agent. Any other component's binding is read-only.

### R5. Accessibility and answers

`@accessibility.label` → `aria-label`, `description` → an `aria-describedby` hidden node, `live` → `aria-live`, `hidden` → `aria-hidden` on the component's host element; explicit values override what the view infers.

Answers go through A2UI actions. The producer (R3) gives each input component `value: {"@path": "/answers/<id>"}` and `action: {"event": {"name": "answer", "context": {"value": {"@path": "/answers/<id>"}, "text": ...}}}` on its send control; the six input schemas in the core catalog gain these two properties (`value` as `DynamicValue`, `action` as `common_types.json#/$defs/Action`; an additive minor bump, `ui-catalogs` C4). On send, the renderer resolves the context bindings and emits the A2UI action message `{"version": "1.0", "action": {"name": "answer", "surfaceId", "sourceComponentId", "timestamp", "context"}}` (`renderer_to_agent.json`) to `onEvent`. With no `onEvent`, controls are disabled like a read-only page.

The host port of `ui-extract` D1 (`ctx.answer`) becomes that adapter: the input views hand it the action message, and the host maps it. Varde's served page supplies a host adapter (in `src/varde/pages/static/`) that maps an `answer` action to its existing POST; a standalone export supplies none. So pages and apps share one answer shape.

### R6. Deferred (each its own later change if the owner wants it)

Catalog functions and `callRendererFunction`/`agentFunctionResponse`; local actions (the `functionCall` form of `Action`) and `event` actions other than `answer`; `@checks` and `ValidationResult`; relative scopes, template `ChildList`, `formatString`; two-way binding outside input components; `sendDataModel`; `inlineCatalogs`; `allowedParents`/`allowedChildren` checks; JSON Schema validation of messages in the browser (the Python producer validates); running `~/source/reference-repos/a2ui/conformance` against this renderer; converging varde pages onto the message renderer (R7, owner question Q-R1).

### R7. Packaging

- `static/components/index.js` (generated by `just catalog`, checked by `just catalog-check`): ESM imports of every view and an object keyed by A2UI name, plus the `prepared` set from the core catalog.
- `static/ui.css` (generated the same way): the token and component CSS in load order, one file for hosts.
- `static/renderer/index.js`: the processor and mount, with no `import` lines, so the classic bundle can include it (the bundle rule of `components.py` `_scoped`: sources carry `export` declarations and no imports). It takes Mithril, the views (inside `catalogs`) and the enhancers as `createRenderer` parameters.
- `static/renderer/entry.js` (generated by `just catalog`, checked by `just catalog-check`): a thin ESM module that imports `index.js`, the views index and the enhancer entry (`blocks.js`) and re-exports `createRenderer` with those filled in, leaving only `m`, `root`, extra catalogs and `onEvent` to the host.
- `package.json` `exports`: `"./renderer"` → `static/renderer/entry.js`, `"./components"`, `"./components/*"`, `"./ui.css"`, `"./catalogs/*"`; `peerDependencies: { "mithril": "2.3.8" }`. Not published (`private: true`) until the owner decides.
- The classic-script bundle of `components.py` gains the import-free `index.js` (not `entry.js`), so `surface_page(messages, title)` (Python) writes one standalone HTML file that inlines the bundle, the CSS and the messages as JSON and calls `createRenderer` with the bundled views and enhancers on load.

Two mount paths in the first version (lead decision, 2026-11-24): served and exported varde pages keep their current mount path (`static/components/mount.js` over Python-rendered mount hosts), and apps and `surface_page` use the message renderer. Both draw through the same views, and the parity test (task 3.5) keeps their markup equal. Converging pages onto the message renderer would remove `mount.js` but needs relative scopes and the rest of R6 for page features (owner question Q-R1); it is listed in R6 as deferred.

## Risks / Trade-offs

- Prepared props make messages bigger and tie full fidelity to the Python producer; R3 states which components work without it.
- An own processor instead of `web_core`: less code to depend on, but no shared conformance; R6 lists the suite as deferred.

## Assumptions

- A1 (high): the host delivers messages (no transport in the library).
- A2 (medium): absolute-path binding is enough for the first app uses.
- A3 (high): the renderer targets evergreen browsers with native ESM.

## Open Questions

- Q-R1 (owner): converge varde pages onto the message renderer once R6 lands, retiring `mount.js`? Recommendation: yes, as its own change after R6; first version keeps two paths (R7).

The JS port question is ui-extract Q2.
