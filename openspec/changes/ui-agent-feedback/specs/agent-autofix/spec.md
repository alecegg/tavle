# Agent autofix

## Purpose

Repair unambiguous authoring slips before rejecting a page, apply the repair in memory in one place, and report every repair back as a warning.

## ADDED Requirements

### Requirement: Names and keys are fixed only with exactly one candidate
The library SHALL fix a component name that differs from exactly one spec name only by case (`fix-component-case`), and an unknown key that has exactly one spec property at difflib ratio 0.8 or higher, absent from the props, in a spec without `extra_keys` (`fix-key-name`). It SHALL apply them inside nested `fields` as well and SHALL change nothing else about names or keys.

#### Scenario: Names and keys
- **WHEN** `fix_result` runs on `Choice(...)` and `table(colums: ["a"])`
- **THEN** the components are `choice` and `table`, the key is `columns`, and `fixes` holds one `Fix` per change with the rule, statement id, property path and a message naming old and new

#### Scenario: Two candidates are left alone
- **WHEN** an unknown key is within the cutoff of two spec properties, or its single match is already present in the props
- **THEN** no `fix-key-name` is made and the `unknown-key` error remains

### Requirement: Values are fixed only with exactly one candidate
The library SHALL turn a decimal string into a number for a `number` property and a whole-number string into a number for an `integer` property (`fix-number-string`), the string `true` or `false` into a boolean for a `boolean` property (`fix-boolean-string`), and a string equal after strip and case folding to exactly one enum member into that member, also for each member of a list of enum values (`fix-enum-case`). It SHALL apply them inside nested `fields` as well.

#### Scenario: Values
- **WHEN** `fix_result` runs on `slider(min: "0", max: 10)`, a `number` property given `"2.5"`, `choice(multiple: "true", ...)` and a property with enum `high` given `"High "`
- **THEN** the values are `0`, `2.5`, `true` and `high`, with one `Fix` each

#### Scenario: Ambiguous values are left alone
- **WHEN** an `integer` property receives `"2.5"` (a `number` property would be fixed), a boolean property receives `"yes"`, or an enum matches two members after case folding
- **THEN** the value is unchanged and the type or enum error remains

#### Scenario: Idempotent
- **WHEN** `fix_result` runs on its own output
- **THEN** the result has no new fixes and equals the input

### Requirement: Cut-off statements are not repaired
A statement that ends before its closing parenthesis SHALL stay an `unterminated` error; no fix SHALL close it.

#### Scenario: Unterminated statement
- **WHEN** a page ends inside `t1 = table(columns: ["a"`
- **THEN** the page check reports `unterminated` and no `fix-*` warning

### Requirement: Fixes apply once, at the page parse
The page layer SHALL apply `fix_result` through `fences.parse_ui_body` (used by `ui_results`), and the page renderer and quality checks SHALL read statements through that same path, so check, render, serve and answer validation see identical fixed statements. The source file SHALL never be rewritten.

#### Scenario: Render matches check
- **WHEN** the same page is rendered
- **THEN** the callout renders as a mounted `callout` component with its title, with no error card

#### Scenario: Answers see the fixed statement
- **WHEN** an input statement written `Choice(...)` receives an answer for its id
- **THEN** the answer validates against its schema and is stored

#### Scenario: One parse path
- **WHEN** `rg -n "parse_lines\(" src/tavle/page src/tavle/comments` runs
- **THEN** the only matches are in `fences.py` and the streaming pending read in `assemble.py`

### Requirement: Fixes are reported as warnings
`page_check.fix_warnings` SHALL build one warning row per fix, and the check assembly SHALL merge them with the quality warnings. Each row's `code` SHALL be the `fix-*` rule, with the statement id and path, and no error SHALL be reported for a slip that was fixed.

#### Scenario: Check reports warnings, not errors
- **WHEN** a page containing `intro = Callout(tite: "x", body: "y")` is checked
- **THEN** `errors` is empty and `warnings` holds `fix-component-case` and `fix-key-name` rows for statement `intro`, and the file's bytes are unchanged

#### Scenario: Stdin check reports fix warnings
- **WHEN** the page above is piped to `tavle check - --json`
- **THEN** `warnings` holds the two `fix-*` rows and any quality warning rows, and `errors` is empty
