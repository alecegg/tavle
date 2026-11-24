# UI catalogs

## Purpose

Describe the page components as A2UI-shaped catalogs in the UI library: one generated catalog for the built-in components, and the format, loading, checks and bundling of agent-authored catalogs. Where varde finds them and how a page picks one is the `pages-catalogs` capability.

## ADDED Requirements

### Requirement: The built-in catalog follows A2UI v1.0 catalog rules
The library SHALL ship `catalogs/core/v1/catalog.json` whose root keys are only those A2UI v1.0 allows, whose `catalogId` equals its `$id`, whose every component has a `component` discriminator constant equal to its key, and whose `$defs` holds `anyComponent` and `anyFunction`.

#### Scenario: Catalog passes the A2UI structural rules
- **WHEN** the library's catalog rule check runs on `catalogs/core/v1/catalog.json` and on the A2UI basic v1 catalog fixture
- **THEN** both pass, and a copy with an extra root key, a component named `Surface`, or a root `oneOf` in a component fails naming the rule

#### Scenario: Every built-in is listed
- **WHEN** the catalog's component names are mapped to ```ui names
- **THEN** they equal the built-in component names plus `stack`, with none missing or extra

### Requirement: The component specs are the one owner of catalog facts
The checked-in catalog and examples SHALL equal what the generator produces from the component specs, and converting each component schema back SHALL give the original property definitions.

#### Scenario: Generated file is current
- **WHEN** `just catalog-check` runs in the library
- **THEN** it exits 0 if and only if the checked-in catalog and examples equal fresh generator output

#### Scenario: Round trip
- **WHEN** every built-in component's properties are converted to JSON Schema and back
- **THEN** the result equals the original definitions

#### Scenario: Unsupported keyword
- **WHEN** a component schema uses `pattern`, `oneOf`, `format` or a numeric bound
- **THEN** loading fails naming the keyword and its path

### Requirement: ```ui statements map to A2UI components without loss
Each ```ui fence SHALL convert to A2UI messages for one surface (a `createSurface`, then an `updateComponents` whose `root` is a `Stack` of the top-level statements), and converting back SHALL give the same statements, with `covers` compared as a set.

#### Scenario: Names and ids
- **WHEN** the statement `my-model = data-model(...)` converts
- **THEN** the component has `id` `my_model` and `component` `DataModel`, and converting back gives `my-model = data-model(...)`

#### Scenario: Page statement refused
- **WHEN** a fence with an `include` statement converts
- **THEN** conversion fails with a message naming `include` as a page statement

#### Scenario: Reserved root id
- **WHEN** a fence with a statement named `root` converts
- **THEN** conversion fails with a message saying `root` is reserved for the surface root

#### Scenario: Covers targets
- **WHEN** a statement has `covers: [other-block, rollout, T3]` where `other-block` is a component in the same fence, `rollout` a heading anchor and `T3` a task id
- **THEN** the component's `covers` prop is `["other_block"]`, `@metadata.extensions.<ui>_covers` is `["rollout", "T3"]`, and converting back gives `covers` with the same three entries

#### Scenario: Covers in every schema
- **WHEN** the core catalog is generated
- **THEN** every component schema has a `covers` property that is an array of `common_types.json#/$defs/ComponentId`

### Requirement: Catalog versions
The catalog major version SHALL be part of its id and path, and a breaking difference between the generated and checked-in catalog SHALL fail unless the major version changed.

#### Scenario: Removing a property needs a new major
- **WHEN** a built-in's property is removed and the generator runs with the same major
- **THEN** `just catalog-check` fails naming the component and property as a breaking change

### Requirement: Custom catalogs
A custom catalog SHALL be a directory with a `catalog.json` header and one folder per component holding `component.json`, `view.js`, `style.css` and at least one `examples/*.ui`; the library SHALL load it, check it, merge it with the core vocabulary and inline the views a page uses in a standalone export.

#### Scenario: Standalone export inlines a used custom component
- **WHEN** the library exports a page that uses `code-compare` from the `review-extras` fixture catalog
- **THEN** the page's single inline script holds that component's view and its stylesheet holds its CSS, and a page that uses no custom component gets the same bundle as before this change

#### Scenario: Built-in names are protected
- **WHEN** a custom catalog defines `Callout` or `Stack`
- **THEN** loading fails naming the clash

#### Scenario: Library check finds a hygiene fault
- **WHEN** `check_catalog` runs on a copy of the fixture whose `view.js` calls `fetch(`, or whose `style.css` has a selector outside `[data-mithril="code-compare"]`
- **THEN** it returns a finding naming the file, the rule and the line
