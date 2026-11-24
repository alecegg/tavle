# Design

## Context

Owner direction (settled 2026-11-24, lead's brief): A2UI-shaped catalogs (fields `catalogId`, `instructions`, per-component JSON Schema, functions where useful); varde pages keep the ```ui syntax mapped onto the same components; built-in plus agent-authored components in per-repo or per-install catalogs, each a Mithril view, JSON Schema props, component-scoped CSS built from theme tokens and worked examples, validated by a check command (schema, render every example, design and a11y probes); a page picks a catalog and a standalone export inlines it.

Runs in `~/source/<ui>` after `ui-extract`; library work only. The varde host side (front matter `catalog:`, catalog discovery, served routes, live refresh, `varde pages catalog`, `varde design catalog-check`, the skill step) is the change `pages-catalogs`, which stays in varde. Paths below use the post-extraction layout (`src/<ui>/blocks/...`).

A2UI sources read (reference clone `~/source/reference-repos/a2ui` at `a337e800`):

- `specification/v1_0/json/catalog_definition.json`: root keys `$schema`, `$id`, `protocolVersion`, `title`, `description`, `catalogId` (required), `metadata.extensions`, `instructions`, `components`, `functions`, `$defs` (with required `anyComponent`, `anyFunction`); `ComponentDefinition` adds `allowedParents`, `allowedChildren`, `metadata`, and forbids root `anyOf`/`oneOf`.
- `specification/v1_0/docs/a2ui_protocol.md:535-775`: naming rules (UAX #31; `Surface` reserved; ids follow the same rule, so `user-card` is invalid), the discriminator rule (`component: {const: <Name>}`), flat components, the allowed external `$ref` targets in `common_types.json` (`ComponentId`, `Child`, `ChildList`, `DynamicString`, ... `FunctionCall`), the strict top-level keys, deprecation annotations (`deprecated`, `x-deprecated-reason`).
- `specification/v1_0/json/common_types.json` `$defs.Extensions`: keys are identifiers; `a2ui_` prefixes are reserved.
- `catalogs/README.md`: catalogs are versioned by major directory (`v1/`) independent of the protocol version; each holds `catalog.json` and `examples/` (A2UI message lists, for example `catalogs/basic/v1/examples/account-balance.json`).
- `catalogs/vegachart/v1/catalog.json`: a catalog with no functions uses `"anyFunction": {"not": {}}`.

Library facts read: `src/<ui>/blocks/spec.py` (`PropertySpec`: `string`, `integer`, `number`, `boolean`, `list`, `object`, `id`, `any`; `required`, `enum`, `items`, `fields`, `nonempty`; `BlockSpec`: `summary`, `notes`, `example`, `validate` (cross-field), `block_type`, `extra_keys`), `blocks/reference.py` (`catalog()` JSON today), `blocks_render/registry.py` (24 props hooks, 6 answer schemas), the parser's id rule `^[a-z][a-z0-9-]{0,47}$` (`lines/parse.py:10`), component names such as `data-model`, `ui-states`, `annotated-code` (kebab case).

## Goals / Non-Goals

**Goals:** a catalog file valid by A2UI v1.0 rules, generated from the specs; a lossless mapping between ```ui statements and A2UI components; custom components with the same contract as built-ins; one check that an agent runs before a page uses a component.

**Non-Goals:** catalog functions (none of today's components needs one); data binding (`ui-app-renderer`); Python prepare hooks for custom components; answers from custom components; publishing catalogs on the web.

## Decisions

### C1. The catalog file is A2UI v1.0 shaped and generated from the specs

`catalogs/core/v1/catalog.json` holds exactly the A2UI root keys: `$schema` (JSON Schema 2020-12), `$id` equal to `catalogId`, `protocolVersion: "1.0"`, `title`, `description`, `catalogId: "urn:<ui>:catalog:core:v1"`, `instructions` (from the hand-written `catalogs/core/instructions.md`), `components`, `functions: {}`, and `$defs` with `anyComponent` (`oneOf` of `#/components/<Name>` plus `discriminator: {propertyName: "component"}`), `anyFunction: {"not": {}}`, and leaf defs only where two components share a value union. Per-component `metadata.extensions` carries the facts A2UI has no field for: `<ui>_blockType` (`BlockSpec.block_type`), `<ui>_prepare` (`"python"` when a props hook exists, else absent), `<ui>_answer` (the answer schema kind and fields for input components), `<ui>_uiName` (the ```ui name), `<ui>_version` (catalog minor version, C4).

Generator `src/<ui>/catalog/core.py` reads `COMPONENT_SPECS`; `just catalog` writes the file and examples; a test fails when the checked-in file differs from the generator (the format forces a file copy for non-Python readers; the test keeps it honest). `varde pages blocks --json` keeps its current shape (its consumers: `code/docs` and the bench) and is not replaced.

`catalogId` is a URN because the library owns no domain; A2UI treats it as an opaque string, and JSON Schema accepts a URN as `$id`. Alternative: an `https://` id under a domain (rejected: none is owned).

### C2. Property mapping (one function each way)

| `PropertySpec` | JSON Schema |
|---|---|
| `string` | `{"type": "string"}`; `enum` → `"enum": [...]`; `nonempty` → `"minLength": 1` |
| `integer`, `number`, `boolean` | the same JSON type |
| `list` with `items` | `{"type": "array", "items": <item>}`; `nonempty` → `"minItems": 1` |
| `object` with `fields` | `{"type": "object", "properties": ..., "required": [...], "additionalProperties": false}` |
| `id` (a reference to another statement) | `{"$ref": "common_types.json#/$defs/ComponentId"}`; a list of ids → `ChildList` |
| `any` | `{}` with the description "checked by the component's own rules" |
| `extra_keys` | `"additionalProperties": <its schema>` (only `ui-states` uses it) |
| `required` | listed in `"required"`, with `"component"` always required |
| generic `covers` (`blocks/check.py` `_covers_faults`, every component) | `"covers": {"type": "array", "items": {"$ref": "common_types.json#/$defs/ComponentId"}}` in every component schema, generated from the generic property, not from each spec; `schema_to_specs` recognises it as the generic property |

The component schema is `{"type": "object", "description": summary + notes, "properties": {"component": {"const": <Name>}, ...}, "required": [...]}`. `schema_to_specs` is the inverse over exactly this keyword subset and rejects any other keyword (`oneOf`, `pattern`, `format`, numeric bounds, ...) with the keyword and path. A test round-trips every built-in. Custom components are validated by the same generic validator through this inverse, so there is one validator. Cross-field rules (`BlockSpec.validate`) have no schema form; built-ins keep them in Python and say so in their description.

### C3. ```ui mapping

- Component name: kebab ```ui name ↔ PascalCase A2UI name (`data-model` ↔ `DataModel`, `ui-states` ↔ `UiStates`, `screen-flow` ↔ `ScreenFlow`). The function in `catalog/names.py` is the one owner; it is a bijection over the built-in names (test) and custom names must be PascalCase identifiers whose kebab form is unused. `names.py` also owns the identifier rule and the reserved names (`Surface`, `Stack`); `rules.py` and `custom.py` import them from there.
- Ids: a ```ui id (`[a-z][a-z0-9-]*`) ↔ A2UI id with `-` replaced by `_` (bijective because `_` is not allowed in ```ui ids).
- A statement `x = callout(tone: "info", text: "...")` ↔ `{"id": "x", "component": "Callout", "tone": "info", "text": "..."}`; references to earlier ids become id strings; container `held` children become their child ids.
- A fence (or page) ↔ one surface: `createSurface` with the core `catalogId`, then one `updateComponents` whose `root` is a new core component `Stack` (`children: ChildList`) listing the top-level statements in order (those no container holds). `Stack` draws its children in page flow with no chrome of its own. `include` is a varde page statement and has no A2UI form; the converter refuses it with a message.
- The `Stack` root has id `root` (A2UI requires exactly one component with that id). `root` is a valid ```ui id, so a statement named `root` is refused with a message saying the id is reserved for the surface root and asking for another name; no renaming happens.
- `covers` (decision by the lead under delegated authority, 2026-11-24): an entry naming a component in the same surface goes in the `covers` prop as a mapped A2UI id. An entry naming anything else (a heading anchor, a task id, a block in another fence) has no A2UI form, so it goes unchanged (no id mapping) in `@metadata.extensions.<ui>_covers` (a schema-valid place: `common_types.json#/$defs/Extensions`). The inverse rebuilds one `covers` list: component ids mapped back, then the extension entries. `covers` is a set (`page_quality.covers_warnings` checks each entry on its own), so the round trip compares it as a set; every other property round-trips exactly.

### C4. Versioning

The catalog major is in the id and the path (`v1`). Additive changes (a new component, a new optional property, a new enum value) bump the minor in `<ui>_version`. A breaking change (removed or renamed component or property, a newly required property, a removed enum value) needs a new major directory, a migration of stored pages in varde (`tests/pages/fixtures/migrate` precedent) and a changelog entry; the old major is deleted with the migration, not kept. A test compares the generated catalog with the checked-in one and, when they differ, fails on a breaking difference unless the major changed. Custom catalogs declare their own `catalogId` and version.

### C5. Custom catalog layout

```
<catalog dir>/
  catalog.json                 # catalogId, title, description, instructions (A2UI root keys; no components)
  components/<Name>/
    component.json             # one A2UI ComponentDefinition (C2 keyword subset)
    view.js                    # export function view(m, props, components, blockId, held); no import lines
    style.css                  # rules scoped to [data-mithril="<kebab name>"]; values from var(--vd-*) tokens
    examples/<case>.ui         # one or more ```ui statements using the component; at least one file
```

The view contract, the no-import rule and the mount host are those of the built-ins (`src/<ui>/components.py`, `static/components/mount.js`). Custom components have no Python prepare step (their props are drawn as written) and no answer schema (they are display-only; `<ui>_blockType` is `visual`). The library merges a custom catalog with core into one vocabulary; a name that clashes with core, or a catalog that uses a reserved name (`Surface`, `Stack`), fails to load.

Where custom catalogs live and how a page picks one is varde policy (`pages-catalogs` design.md P1).

### C6. Trust model

A custom view is local, agent-written JavaScript running in the page: the same trust as agent-written HTML, which the owner already accepts for scratch pages. Served pages load it as a file from the page server, so the CSP `script-src 'self'` (`server_parts.py`) is unchanged; a standalone export inlines it inside the one bundle script. The static gates refuse, as hygiene and not as a sandbox: `import`/`export` forms other than the declared `view`, `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `eval`, `new Function`, `document.cookie`, `localStorage`, `sessionStorage`, `</script`, and CSS `url(`, `@import`, `@font-face`. No network access is needed or allowed by the page CSP anyway.

### C7. Library checks

The library gives the pieces the varde check command (`pages-catalogs` P3) runs:

1. `check_catalog(dir)`: root keys and names (identifier rule, `Surface`/`Stack` reserved, no clash with core), the discriminator, flat components, allowed `$ref` targets, the C2 keyword subset, deprecation keys well formed; every example parses and its statements validate; JS and CSS hygiene (C6); CSS selectors scoped to the component. Findings are `(path, rule, message)` with file and line where one exists. The design-token rule is varde's (`token_rules.py`) and runs in the command.
2. `catalog_example_page(catalog)`: one standalone page holding every example, which the command's render and design gates open.

## Risks / Trade-offs

- `additionalProperties` with a schema on `UiStates` is not forbidden by A2UI v1.0 rules but no A2UI catalog uses it; if an A2UI validator rejects it, `ui-states` needs a list form (a breaking change, C4).
- Checked-in generated JSON is a second copy; the parity test is the guard.
- The hygiene list is not a sandbox; the trust statement (C6) is the real boundary.

## Assumptions

- A1 (high): no built-in component needs an A2UI function now; `functions` stays empty.
- A2 (medium): custom components are display-only; inputs stay built-in. If the owner wants custom inputs, a later change adds answer schemas to `component.json` metadata.
- A3 (high): a URN `catalogId` is acceptable.
- A4 (high): `covers` order carries no meaning, so returning component entries first after a round trip loses nothing (C3).

## Open Questions

None for this change; the owner questions are in `ui-extract` design.md.
