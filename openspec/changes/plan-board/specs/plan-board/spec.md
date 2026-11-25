# Plan board

## Purpose

Tables and sections for pages that track work: where table controls sit, progress columns, hiding finished rows, and collapsible sections.

## ADDED Requirements

### Requirement: Table toolbar sits above the rows
A `table` block's toolbar (filter field, phone sort select, hide-done switch, total progress) SHALL render before the table's scroll region. The "Show all rows" toggle SHALL render after it.

#### Scenario: Toolbar order
- **WHEN** a table with 12 rows is rendered
- **THEN** the `.vb-filterbar` element precedes the `.vb-scroll` element in document order and `.vb-more` follows it

### Requirement: Tables never scroll sideways
A table that stacks (no `stack: false`) SHALL show its rows as cards whenever its grid would be wider than its region, at any viewport width. Status, badge and code cell text SHALL wrap; number cells SHALL stay on one line.

#### Scenario: Unbreakable text at a narrow desktop width
- **WHEN** a 4-column table with a 60-character path in a text cell is shown at 700px
- **THEN** its rows show as cards and neither the page nor the table region scrolls sideways; at 1400px it shows as a grid

### Requirement: Progress column
A column typed `progress` SHALL take cells that are `[done, total]` pairs of non-negative integers with done at most total; any other cell SHALL be a `type` fault. Each cell SHALL show a bar filled to done/total and the text "done of total". Sorting SHALL order by done/total. A table with a progress column SHALL show one total bar above its rows, labelled with the summed done and total of every row, hidden rows included.

#### Scenario: Cells and total
- **WHEN** a table has a progress column with cells `[1, 2]` and `[3, 6]`
- **THEN** the cells read "1 of 2" and "3 of 6" with bars at 50%, and the total bar reads "4 of 8" at 50%

#### Scenario: Bad cell
- **WHEN** a progress cell is `[5, 3]` or `"5"`
- **THEN** check reports a `type` fault naming the row and column

### Requirement: Hide done switch
A table with `hide_done` set SHALL show a "Hide done" switch in its toolbar, on when `hide_done` is `true` and off when `false`. While on, rows whose `status` cell has the `ok` kind SHALL be hidden, and the toolbar SHALL say how many are hidden. The filter and the switch SHALL combine.

#### Scenario: Default on
- **WHEN** a table with `hide_done: true` has 3 rows and one has status "done"
- **THEN** 2 rows show, the switch is on, and the toolbar reads "1 done hidden"; turning the switch off shows 3 rows

### Requirement: Collapsible sticky sections
A page with front matter `sections: collapsible` SHALL give each `##` heading a button with `aria-expanded` that hides and shows the blocks after it up to the next `#` or `##` heading, and `##` headings SHALL stay at the top of the viewport while their section scrolls. Printing SHALL show every section. Pages without the key SHALL be unchanged.

#### Scenario: Collapse a section
- **WHEN** the reader presses the button on a `##` heading
- **THEN** the blocks of that section hide, `aria-expanded` is `false`, and the next section's heading still shows

#### Scenario: Sticky heading
- **WHEN** the reader scrolls into the middle of a long section
- **THEN** that section's `##` heading is at the top of the viewport

### Requirement: Plan board template
The `varde-visualize` skill SHALL ship `assets/plan-board.md`, a page with front matter `sections: collapsible`, a stats strip, and tables using `progress`, `status` and `hide_done: true`, which passes `varde pages check`.

#### Scenario: Template checks
- **WHEN** `varde pages check` runs on `assets/plan-board.md`
- **THEN** it reports no errors
