# Agent errors

## Purpose

Give an agent that writes tavle pages errors it can act on: a location, the statement, the valid alternatives, a stable rule name from a published list, and a validate-only entry that prints JSON.

## ADDED Requirements

### Requirement: Statement-level errors carry line and statement id
Every error attached to a `ui` statement SHALL carry the document line and the statement id, in its text form (a suffix ` (statement 'ID')` after the existing `line N: rule: message`) and in its JSON row (`line`, `statement_id`). An error with no statement (a heading or fence finding, or an `id-invalid` error whose id is not valid) SHALL carry an empty `statement_id`.

#### Scenario: Component fault names its statement
- **WHEN** `check_props("table", {"rows": 3}, 4, "t1")` runs and the error text is read
- **THEN** it starts with `line 4: type: ` and ends with ` (statement 't1')`, and the `BlockError` has `statement_id` `t1`

#### Scenario: Parse error names its statement
- **WHEN** `parse_lines('t1 = table(columns: ["a"] rows: 1)')` fails with `syntax`
- **THEN** the error has `statement_id` `t1` and its text ends with ` (statement 't1')`

#### Scenario: Rendered error card shows the id
- **WHEN** `render_block("table", {"rows": 3}, "t1", 4)` renders
- **THEN** the card text contains `(statement 't1')`

#### Scenario: Container fault names the container
- **WHEN** `container_errors` reports a tab holding an input component
- **THEN** each tuple has four elements and the fourth is the container's statement id

#### Scenario: Page-level findings have no statement
- **WHEN** a page check reports a duplicate heading id
- **THEN** the row's `statement_id` is `""` and its line is the heading's line

### Requirement: Unknown and wrong values list valid options and the closest match
An `unknown-key` fault, an enum value fault and a `component-unknown` error SHALL carry `valid` (every valid name) and `closest` (the best match above the cutoff, else empty), and their message SHALL end with the note produced by the one suggester, naming at most 12 valid names and the count of the rest.

#### Scenario: Close key
- **WHEN** a `table` statement has the key `colums`
- **THEN** the fault has rule `unknown-key`, `closest` `columns`, `valid` listing the table's keys, and a message containing `closest: 'columns'`

#### Scenario: Enum value
- **WHEN** a property with enum `low, medium, high` receives `"hgh"`
- **THEN** the fault has `valid` `("low", "medium", "high")` and `closest` `high`

#### Scenario: Unknown component is capped
- **WHEN** a statement names the component `chrt`
- **THEN** the error has `closest` `chart`, `valid` holding every component name, and a message listing 12 names followed by `(+N more)` with N equal to the rest

#### Scenario: Theme messages are unchanged
- **WHEN** the theme layer rejects an unknown token or preset
- **THEN** its message is byte-identical to the message before this change (`tests/test_theme_layers.py` passes unchanged)

### Requirement: Rule names are one published list
The library SHALL publish `RULES`, mapping every rule name an error or warning can carry to its severity (`error` or `warning`) and a one-line summary, and `tavle rules [--json]` SHALL print it. A rule name emitted anywhere in the library and missing from `RULES`, or listed and never emitted, SHALL fail the test suite. Existing rule names SHALL NOT be renamed by this change.

#### Scenario: Registry matches the code
- **WHEN** `uv run pytest tests/test_rule_names.py` runs
- **THEN** it passes, and adding a `Fault("new-rule", ...)` call without a `RULES` entry makes it fail naming `new-rule`

#### Scenario: Rules verb
- **WHEN** `tavle rules --json` runs
- **THEN** it prints rows `{name, severity, summary}` for every `RULES` key, sorted by name, and exits 0

### Requirement: A validate-only entry reads stdin and prints JSON
`tavle check -` SHALL read the page text from standard input, run the same check as `tavle check DOC`, resolve no includes, and with `--json` print `{"errors": [...], "warnings": [...]}` whose rows hold `code`, `line`, `statement_id`, `path`, `message`, `valid` and `closest`. The exit code SHALL be 1 when there are errors and 0 otherwise.

#### Scenario: Piped page with an error
- **WHEN** a page with a table whose `rows` is `3` is piped to `tavle check - --json`
- **THEN** the output holds one error with `code` `type`, `statement_id` `t1`, `path` `rows`, and the exit code is 1

#### Scenario: Piped clean page
- **WHEN** a page with no errors is piped to `tavle check - --json`
- **THEN** `errors` is `[]` and the exit code is 0
