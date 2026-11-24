# UI app renderer

## Purpose

Let a host page render the library's components from A2UI v1.0 messages with Mithril, and let the library produce those messages and standalone pages from them.

## ADDED Requirements

### Requirement: Supported messages
The renderer SHALL accept A2UI v1.0 `createSurface`, `updateComponents`, `updateDataModel` and `deleteSurface` messages, and SHALL report any other message or version as an `unsupported-message` event without changing state or throwing.

#### Scenario: Surface lifecycle
- **WHEN** a host processes `createSurface` for `s1` with the core catalog, then `updateComponents` with a `Stack` root holding a `Callout`, then `deleteSurface` for `s1`
- **THEN** the callout is drawn after the second message with the same markup a varde page gives that callout, and nothing of `s1` remains after the third

#### Scenario: Root buffering
- **WHEN** `updateComponents` sends a `Callout` before any component with id `root`
- **THEN** nothing is drawn until a later message defines `root`

#### Scenario: Unsupported message
- **WHEN** the host processes a `callRendererFunction` message or a message with `version` `"0.9"`
- **THEN** `onEvent` receives `unsupported-message` and no surface changes

### Requirement: Capabilities and catalog resolution
The renderer SHALL report `{"1.0": {"supportedCatalogIds": [...]}}` listing the core catalog and every catalog passed in, and SHALL resolve each component by its `@catalogId`, else the surface `catalogId`, with no fallback.

#### Scenario: No fallback
- **WHEN** a surface created without `catalogId` receives a component with no `@catalogId`
- **THEN** the component is not drawn and `onEvent` receives `unresolved-catalog`

### Requirement: Prepared props
Components the catalog marks as prepared SHALL draw from `@metadata.extensions.<ui>_drawn`; without it they SHALL draw an error card and report `needs-prepare`. The library's Python producer SHALL attach `<ui>_drawn` for every prepared component.

#### Scenario: Producer output draws like a page
- **WHEN** the producer converts the every-block test page's fences and the renderer processes the messages in jsdom
- **THEN** every component mounts and each one's markup equals the varde page mount of the same statement

#### Scenario: Missing drawn props
- **WHEN** a `Chart` component arrives without `<ui>_drawn`
- **THEN** an error card is drawn in its place and `onEvent` receives `needs-prepare`

### Requirement: Data model binding
`updateDataModel` SHALL set or delete the value at its JSON Pointer path and re-render the surface; a property value `{"@path": "/..."}` (A2UI v1.0 `DataBinding`) with an absolute path SHALL draw the model value in components with no prepare step, an input component's `value` binding SHALL be written locally when the user changes the control, and any other binding form SHALL draw an error card and report `unsupported-binding`.

#### Scenario: Bound text updates
- **WHEN** a `Callout` has `text: {"@path": "/note"}` and `updateDataModel` sets `/note` to "Ready"
- **THEN** the callout text reads "Ready"

#### Scenario: Input writes its binding locally
- **WHEN** a `Choice` has `value: {"@path": "/answers/pick"}` and the user picks "approve" without sending
- **THEN** the model at `/answers/pick` is "approve" and `onEvent` receives no action message

### Requirement: Accessibility and answers
The renderer SHALL map `@accessibility` `label`, `description`, `live` and `hidden` to ARIA on the component's host, overriding inferred values, and SHALL report input answers as A2UI v1.0 action messages (`renderer_to_agent.json`), disabling controls when the host gives no event handler.

#### Scenario: Explicit label wins
- **WHEN** a component has `@accessibility.label` "Release risks"
- **THEN** its host has `aria-label="Release risks"`

#### Scenario: Answer event
- **WHEN** the user picks an option in a `Choice` component whose `action` is `{"event": {"name": "answer", "context": {"value": {"@path": "/answers/pick"}}}}` and sends it
- **THEN** `onEvent` receives `{"version": "1.0", "action": {"name": "answer", "surfaceId", "sourceComponentId", "timestamp", "context": {"value": <the picked option>}}}`

### Requirement: Packaging and standalone pages
The library SHALL expose the renderer, views, generated component index, CSS and catalogs through its `package.json` `exports`, with Mithril passed in by the host, and SHALL build one self-contained HTML file from a message list.

#### Scenario: Standalone page from messages
- **WHEN** `surface_page(messages, title)` writes a file and it opens in Chromium with network disabled
- **THEN** every component mounts with no console error and no request leaves the page

#### Scenario: Generated index is current
- **WHEN** `just catalog-check` runs
- **THEN** it fails if `static/components/index.js`, `static/renderer/entry.js` or `static/ui.css` differs from fresh generator output

#### Scenario: Renderer core has no imports
- **WHEN** `static/renderer/index.js` is read
- **THEN** it has no `import` line, and `package.json` `exports["./renderer"]` names `static/renderer/entry.js`
