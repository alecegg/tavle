# Sensitive fields

## Purpose

Keep a secret typed into a form out of the comment log, the page's thread HTML and every reader the agent uses, while still telling the agent whether the field was filled.

## ADDED Requirements

### Requirement: `sensitive` is a text-field key of `form`
A `form` field of type `text` SHALL accept `sensitive` as a boolean. On any other field type, `sensitive` SHALL fault as `unknown-key` with the valid keys for that type; a non-boolean value SHALL fault as `type`.

#### Scenario: Accepted and refused
- **WHEN** `check_props("form", ...)` runs with `sensitive: true` on a text field, on a number field, and with `sensitive: "yes"` on a text field
- **THEN** the first returns no error, the second returns `unknown-key` with `valid` for number fields, and the third returns `type` at path `fields[1].sensitive`

### Requirement: A sensitive field draws as a password field
The form view SHALL draw a sensitive text field as `<input type="password" autocomplete="off" spellcheck="false" data-sensitive>`, never as a textarea, and SHALL persist no draft value.

#### Scenario: Markup
- **WHEN** a form with a sensitive text field of `maxlength` 500 is mounted
- **THEN** that field is an `input` of type `password` with `autocomplete="off"`, and no `textarea` exists for it

### Requirement: The value is replaced by a presence marker before it is stored
After the answer validates and before any text is synthesized or stored, `redact_form_value(shape, value)` SHALL replace each sensitive field's value with `{"redacted": true, "present": <bool>}`, `present` being whether the submitted text was non-empty. The stored row, the thread HTML, `comments --json`, the envelope and the watch line SHALL NOT contain the value. The value SHALL NOT be stored elsewhere. Fields not marked sensitive SHALL be unchanged.

#### Scenario: Secret never lands on disk
- **WHEN** a form with sensitive field `token` and plain field `user` is answered with `token` `s3cret-value` and `user` `bob` over HTTP
- **THEN** the bytes of `<doc>.comments.jsonl` do not contain `s3cret-value`, the row's value is `{"user": "bob", "token": {"redacted": true, "present": true}}`, and the row's `text` does not contain it

#### Scenario: Empty sensitive field
- **WHEN** the optional sensitive field is submitted empty
- **THEN** its marker has `present` false

#### Scenario: Required still enforced
- **WHEN** a required sensitive field is submitted empty
- **THEN** the answer is refused with the existing required-field error before any redaction

#### Scenario: Readers
- **WHEN** the page is re-rendered and `tavle comments --json` runs after the answer
- **THEN** neither output contains `s3cret-value`; nor do the envelope, the watch line or the POST response

#### Scenario: Invalid sensitive refuses the answer
- **WHEN** a form statement has `sensitive: "yes"` on a text field and an answer is posted
- **THEN** the answer is refused (`answers._statement_props` finds no schema) and nothing is stored

### Requirement: The threat model is written down
The documentation SHALL state that the flag controls what reaches the log and the agent, and that it does not protect against a hostile page author, browser autofill history, other local users of a running server, or access to its memory.

#### Scenario: Doc check
- **WHEN** `rg -n "hostile page author" docs/agent-feedback.md` runs
- **THEN** it matches the threat-model paragraph
