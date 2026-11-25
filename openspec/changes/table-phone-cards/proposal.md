# Proposal

## Why

The owner, viewing report pages on a phone: tables should not scroll sideways on mobile; show rows as cards or another layout. Today a markdown table always scrolls sideways, and a `table` block shows rows as labelled pairs only when the author sets `stack: true`.

## What Changes

- At phone width (the existing `max-width: 40rem` breakpoint), each row of a `table` block shows as a card: one label and value pair per column, a full border and radius, and space between cards. Nothing scrolls sideways.
- The `table` block stacks by default. `stack: false` keeps the scrolling grid for tables where comparing across columns matters (wide numeric matrices).
- Markdown tables stack the same way: the renderer labels each cell with its column header, and the same card rules apply.
- Other scrolling blocks (option matrix, diff, ER fields, code) are out of scope.

## Capabilities

### New Capabilities

- `table-phone-cards`: phone layout of `table` blocks and markdown tables.

## Impact

- `src/tavle/static/css/40-table.css`, `src/tavle/static/components/table.js`, `src/tavle/blocks/tables.py` (the `stack` description), `src/tavle/page/render.py` (`_parse_table`).
- Served and exported HTML of markdown tables gains `data-label` attributes and a class; checked-in goldens that contain a markdown table change by those additions only.
- Varde pages pick this up through the tavle dependency; no varde code change.
