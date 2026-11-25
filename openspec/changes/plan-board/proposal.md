# Proposal

## Why

The owner, on the build-queue report page: "move filters and sort to the top of the area, add a toggle for hiding done items and enable by default, add a bar for total progress on all items and each card, make sections collapsible and sticky section headers. Then save the page as a template for future use", named like "plan board".

## What Changes

- Every `table` block shows its toolbar (filter, phone sort select) above the rows instead of below. The "Show all rows" toggle stays below.
- New column type `progress`: a cell is `[done, total]`; it shows a bar and "done of total". A table with a progress column shows a total bar above its rows that sums every row.
- New table property `hide_done` (boolean): adds a "Hide done" switch to the toolbar, on when `true`. A row is done when a `status` cell reads as done (the `ok` status kind).
- New front matter key `sections: collapsible`: each `##` heading gets a collapse button for the blocks up to the next `#` or `##` heading, and `##` headings stick to the top of the viewport while their section scrolls.
- A "plan board" page template in the `varde-visualize` skill (`assets/plan-board.md`) that uses all of the above; the build-queue report page moves onto it.

## Capabilities

### New Capabilities

- `plan-board`: table toolbar placement, progress columns, hide-done switch, collapsible sticky sections, and the plan board template.

## Impact

- tavle: `src/tavle/static/table.js`, `src/tavle/static/components/table.js`, `src/tavle/blocks/tables.py`, `src/tavle/static/css/40-table.css`, `src/tavle/page/render.py` (front matter flag on the page), a page script and stylesheet for sections.
- varde: `src/varde/pages/help/blocks.txt` (checked copy of the table help text), `src/varde/skills/varde-visualize/` (template asset and one SKILL.md line).
