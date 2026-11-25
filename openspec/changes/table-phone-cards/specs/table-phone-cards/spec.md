# Table phone cards

## Purpose

How tables lay out at phone width.

## ADDED Requirements

### Requirement: Tables show rows as cards at phone width
At viewport widths of 40rem and below, a `table` block without `stack: false`, and every markdown table, SHALL show each body row as a card of label and value pairs, one pair per column, and SHALL NOT scroll sideways.

#### Scenario: Block table on a phone
- **WHEN** a page with a five-column `table` block (no `stack` property) is rendered at 375px wide
- **THEN** each body row is a block-level card with a full border, each cell shows its column label, and the table's `scrollWidth` is at most its `clientWidth`

#### Scenario: Markdown table on a phone
- **WHEN** a page with a five-column markdown table is rendered at 375px wide
- **THEN** each body cell carries `data-label` equal to its column header's text, each row is a card, and the table's `scrollWidth` is at most its `clientWidth`

#### Scenario: Opt out keeps the grid
- **WHEN** a `table` block sets `stack: false` and is rendered at 375px wide
- **THEN** it keeps the scrolling grid it has today

#### Scenario: Wide screens unchanged
- **WHEN** either table kind is rendered at 1024px wide
- **THEN** it renders as a grid, as before
