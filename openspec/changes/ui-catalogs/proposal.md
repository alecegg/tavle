# Proposal

## Why

The owner wants a catalog scope like A2UI's (https://a2ui.org/concepts/catalogs): one machine-readable catalog of the built-in components, and agent-authored components in per-repo or per-install catalogs, so an agent can add richer graph views, code comparisons or styles than the fixed vocabulary allows, each checked before a page uses it. Today the vocabulary is fixed in code and its JSON listing (`varde pages blocks --json`) is a varde-specific shape.

## What Changes

- The library generates an A2UI v1.0 shaped catalog (`catalogId`, `instructions`, per-component JSON Schema, `$defs.anyComponent`, `$defs.anyFunction`) for the built-in components from the existing component specs, which stay the one owner of property facts. The generated file and one example per component are checked in and kept equal to the generator by a test.
- The library converts ```ui statements to A2UI components and messages (names, ids, child references), adding a `Stack` component as the surface root.
- Custom catalogs: a directory holding a catalog header and per-component folders (JSON Schema props, a Mithril view, component-scoped CSS built from theme tokens, worked examples). The library loads, validates and bundles them; built-in names cannot be overridden.
- The library gives the static catalog check and a page of every example, which varde's check command runs.
- Varde-side work (discovery, front matter `catalog:`, served routes, `varde pages catalog`, `varde design catalog-check`, the skill step) is the separate change `pages-catalogs`, which stays in varde.

## Capabilities

### New Capabilities

- `ui-catalogs`: the catalog format, the built-in catalog, the ```ui mapping, custom catalog contents, trust, loading and the library checks.

### Modified Capabilities

(none)

## Impact

- Library (`~/source/<ui>`): new `catalog/` package, `Stack` component, generated `catalogs/core/v1/`, bundle and export accept extra catalogs.
- Varde: none in this change (see `pages-catalogs`).
- No change to existing pages or their output.
- Depends on `ui-extract` (the library exists) and `varde-pages-themes` (component CSS reads its tokens).
