# Answer envelope

## Purpose

Give an agent one typed record per answer: which control fired, the values by statement id, the decision, the comment, who decided, and which required inputs are still open.

## ADDED Requirements

### Requirement: Input components take a `required` prop
`choice`, `form`, `comment`, `ranking`, `slider` and `decision` SHALL accept `required` as a boolean; any other value SHALL fault with rule `type`. A required input SHALL show a `Required` badge in the page.

#### Scenario: Spec accepts the prop
- **WHEN** `check_props("choice", {..., "required": true}, 1)` runs
- **THEN** it returns no error, and `required: "yes"` returns a `type` fault with path `required`

#### Scenario: Badge
- **WHEN** a required `choice` is mounted in the component test harness
- **THEN** its root contains one `.vb-required` element reading `Required`, and an optional one contains none

### Requirement: The envelope has one fixed shape
`answer_envelope(doc_text, rows, answer_id)` SHALL return `{version: 1, answer_id, ts, control: {id, action}, decision, comment, decided_by, values, required_open}` and SHALL NOT read or write files. `control.id` is the answered statement id; `action` is `send` except for `decision`, where it is the verdict (`approved`, `denied`, `commented`); `decision` is that verdict for a decision component and `null` otherwise.

#### Scenario: Shape and purity
- **WHEN** `answer_envelope` runs on a page and rows held in memory, with file access patched to fail
- **THEN** it returns a dict with exactly the keys `version`, `answer_id`, `ts`, `control`, `decision`, `comment`, `decided_by`, `values` and `required_open`, and `version` is `1`

### Requirement: Envelope fields are derived from the rows up to the answer
`comment` SHALL be the row text, or empty when it equals the default synthesized from value and item. `values` SHALL map each answered statement id to its latest value among the rows up to and including `answer_id`, in log order. `required_open` SHALL list, in statement order, the ids of required inputs with no answer row among those rows. `decided_by` SHALL be `rule` when the row's `actor` starts with `rule:`, else `person`.

#### Scenario: Choice answered, another required input open
- **WHEN** a page has required `pick` (choice) and required `notes` (comment), and one answer row exists for `pick`
- **THEN** the envelope has `control` `{id: "pick", action: "send"}`, `values` `{pick: ...}`, `required_open` `["notes"]`, `decision` null and `decided_by` `person`

#### Scenario: Decision verdict
- **WHEN** the row answers a `decision` statement with `denied` and a typed comment
- **THEN** `control.action` and `decision` are `denied` and `comment` is the typed text

#### Scenario: Default text is not a comment
- **WHEN** the row text is the synthesized `"<value>: <item>"`
- **THEN** `comment` is `""`

#### Scenario: Latest answer wins, as of the row
- **WHEN** two answer rows exist for `pick`, and the envelope is built for the first
- **THEN** `values.pick` is the first row's value

### Requirement: Rule-decided answers are stored through one validated write
`store_answer(doc, anchor, item, value, text, actor)` SHALL validate and store an answer exactly as the HTTP path does, with `actor` of `user` or a name matching `^rule:[a-z0-9-]{1,48}$`; any other actor SHALL raise `ValueError`. The HTTP handler SHALL call it with `user`. A stored `rule:` row SHALL give `decided_by` `rule` in its envelope.

#### Scenario: Rule answer
- **WHEN** `store_answer(..., actor="rule:auto-approve")` stores an approval
- **THEN** the row's `actor` is `rule:auto-approve` and its envelope's `decided_by` is `rule`

#### Scenario: Bad actor
- **WHEN** `store_answer(..., actor="agent")` runs
- **THEN** it raises `ValueError` and nothing is appended

### Requirement: Answer rows in comment listings carry the envelope
Each answer row returned by `filtered_comments` (and so by `tavle comments --json`) SHALL carry an `envelope` key; other rows SHALL NOT. Stored rows SHALL keep their current fields.

#### Scenario: Filtered listing keeps the envelope
- **WHEN** two required inputs are answered and `tavle comments DOC --json --kind answer --open` runs
- **THEN** each returned answer row's envelope has the same `required_open` as in the unfiltered listing

#### Scenario: Legacy decision row
- **WHEN** a stored row has the legacy `decision` form with a `verdict`
- **THEN** its envelope has `decision` set to that verdict and `values` read through `answer_value`

#### Scenario: Listing
- **WHEN** a person answers a required input over HTTP and `tavle comments DOC --json` runs
- **THEN** the answer row has an `envelope` with the answered id in `values` and the other required inputs in `required_open`, and the log line on disk has no `envelope` key
