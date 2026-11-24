# Design

## Context

Decision authority: the lead settled every choice below under the owner's standing delegation (2026-11-25); each has a reason and the alternatives it beat. No open question or assumption remains.

Evidence (tavle `d230167`, varde `aa398018`; line numbers from those trees; page-layer paths in varde move to tavle under `pages-extract` D1):

- Errors today. `BlockError(line, rule, message, statement_id="", path="")` (`src/tavle/blocks/check.py:86-95`) and `Fault(rule, message, path)` (`blocks/rules.py:6-10`) already exist; varde-pages-design-system 4.1a/4.1b added them. `check_props` takes `statement_id` (`check.py:176-189`), but `render_block` calls it without one (`blocks_render/__init__.py:46`), `BlockError.text()` prints only line, rule and message (`check.py:94`), and `ParseError(line, rule, message)` (`lines/parse.py:37-44`), `container_errors` tuples (`blocks/containers.py:140-147`) and `include_errors`/`heading_id_errors` tuples (`varde/src/varde/pages/include.py:274`, `select.py:241`) carry no id. `unknown-key` faults name only the key (`check.py:121`, `rules.py:31-34`, `inputs.py:200-207`); enum faults list the options without a closest match (`check.py:160-162`); `component-unknown` lists every component (`check.py:186-188`). The only difflib use is the theme layer (`theme/layers.py:24,36`).
- JSON check output exists: `varde pages blocks --check --json` prints rows `{code, line, statement_id, path, message}` (`varde/src/varde/pages/operations.py:222-251`), pinned by `tests/pages/test_check_json.py`. `pages-extract` D4/D12 move this to `tavle check DOC --json` and `listings.py`. The report's claim that component faults lack statement id and line is stale for `props_errors`; the gaps are the ones above.
- Rule names are 86 distinct literals in `Fault(...)`, `ParseError(...)`, `fail(...)` calls across `lines/` and `blocks/` (an AST scan finds 86 distinct literals, plus three non-literal pass-through sites: `f.rule` in `check.py`, `fail.rule` in `parse.py`, `rule` in `containers.py`), plus page-layer literals in varde `page_check.py`, `page_quality.py`, `include.py`, `select.py`. There is no list.
- Answers today are one row per input: `store._store_answer` (`varde/src/varde/pages/store.py:135-150`) validates with `answers.validate_answer`, then `comments.append_comment` writes `{id, ts, anchor, quote, text, state, actor: "user", kind: "answer", item, value}` to `<doc>.comments.jsonl` (`comments.py:131-156`); `mark_latest_decisions` adds `latest` on read (`:216-226`). `text` is the typed note or, when empty, `"<value>: <item>"` (`store._answer_text`, `:130`). There is no page-level submit (`rg -i submit` finds only the `submit` label prop of `form` and `comment`, and the comment editor's own Send and Save buttons in varde's `app.js`), no control field, no required flag on any input component (only form fields have `required`, `inputs.py:289-315`), and no rule actor (`actor` defaults to `user`; replies use other actors). The decision verdicts are `approved`, `denied`, `commented` (`blocks_render/decision.py:12`); there is no dismiss control.
- Redaction today: none. `CONTROLS` strips control and bidi characters only (`limits.py`). A form answer's value, including every field, is stored whole and echoed into `text` through `json.dumps(value)` (`store.py:130-132`).
- Statement flow: every consumer of page `ui` text parses through `fences.ui_results` (`varde/src/varde/pages/fences.py:89`), except `render._ui_fence` (`render.py:449-453`), `page_quality` (`:68-82`) and the streaming `pending` read (`assemble.py:131`).

## Goals / Non-Goals

**Goals:** the four feedback surfaces, published as stable interfaces with one owner each; no behaviour change for a page that is valid today; the behaviors decision doc.

**Non-Goals:** the generated agent reference and catalog (`ui-catalogs`, item 5); the A2UI renderer (`ui-app-renderer`); MCP Apps output; theming interop; repairing mid-stream cut-offs; a sensitive-value hand-off; the varde command wiring (queued, task 6.1).

## Decisions

### E1. Error record: add `valid` and `closest`, keep the rest and the JSON key `code`

`Fault` and `BlockError` gain `valid: tuple[str, ...] = ()` and `closest: str = ""` (trailing defaults, so the roughly 178 `Fault(rule, message, path)` call sites keep working). The JSON row keeps `code`, `line`, `statement_id`, `path`, `message` (pinned by varde's test) and adds `valid` (list) and `closest` (string). Severity is the list the row sits in (`errors`, `warnings`), as today; no per-row `severity` field (a second copy of one fact).

Why: additive, and varde's pinned keys survive. Rejected: renaming `code` to `rule` (breaks the pin and the report's own consumers for no gain); a `severity` field (duplicates list membership).

### E2. One suggester owns closest match and the option note

`src/tavle/suggest.py` holds `close_matches(word, valid, limit=3, cutoff=0.6)` and `valid_note(valid, close)`. The note is `; closest: 'x'; valid: a, b, ... (+N more)` with at most `MAX_SHOWN = 12` names; the structured `valid` always holds all names. The theme layer (`theme/layers.py:24,36`) switches to `close_matches` with its current limits so its messages stay byte-identical, which removes the second difflib copy. The autofix key rule (A2) uses the same function.

Why: one owner for "closest" (the user's single-owner rule) and a cap against message bloat, which the report named as the risk. Rejected: a per-module difflib call (two behaviors that would drift).

### E3. Statement id on every statement-level error; the id goes in a suffix

- `BlockError.text()` and `ParseError.text()` append ` (statement 'ID')` when an id exists, so the existing prefix `line N: rule: ` is unchanged (`tests/test_lines_parse.py:106` and varde's `startswith` check keep passing). The varde-style line `DOC:LINE: RULE: MESSAGE` gets the same suffix.
- `render_block` passes its `block_id`, so error cards show the id.
- `ParseError.statement_id` is set when the failing statement's id token was valid (`id-invalid` has none: its message holds the text). The parser records the id after `ID_RULE` passes in `_statement` (`parse.py:269-293`).
- `container_errors` returns `(line, rule, message, statement_id)`; varde builds `BlockError(*found)`, and `statement_id` is `BlockError`'s fourth field, so the change is compatible. The id is the container's id.
- Page layer (after `pages-extract`): `include_errors` and `heading_id_errors` return `BlockError` (an include statement has an id; a heading error has none, so its `statement_id` is `""`). "Every error" therefore means every error attached to a statement; page-level findings (fences, headings) carry line and rule only, and the spec says so.

Why: suffix keeps old parsers working. Rejected: a prefix or bracket form (breaks `startswith`); putting ids in `path` (a different fact).

### E4. The rule registry is one data module plus a scan test

`src/tavle/rule_names.py` holds `RULES: Mapping[str, Rule]` (`Rule(severity, summary)`, severity `error` or `warning`). The rule literals stay at their call sites (178 sites; changing them to constants is churn with no behavior gain). `tests/test_rule_names.py` scans `src/tavle` with `ast` for the first literal of `Fault`, `Fix`, `fail` and the second of `ParseError`, `BlockError`, and fails on any literal missing from `RULES` or any `RULES` key never emitted (the tool forces a copy, so the copy is checked, per the owner's rule). After `pages-extract` the scan widens to `page/` and `comments/`. Existing rule names are not renamed or split (`type` still covers type, enum and empty faults); the registry summary says what each covers.

Why: renames would break pinned records and varde consumers; the structured `valid`/`closest` fields give the agent the missing detail. Rejected: an enum of rules with call-site rewrites (large churn); generating the list at runtime from the scan (production code would depend on `ast` over its own source).

### E5. Validate-only entry is `tavle check -` with JSON

`tavle check DOC [--json]` is `pages-extract` D4's. This change makes `DOC` of `-` read text from stdin (includes are not resolved, as with `root=None` in `page_check.check`) and adds `tavle rules [--json]` (name, severity, summary). The library function is the one `page_check.check` already is. `--json` prints `{"errors": [...], "warnings": [...]}` with the E1 rows. Varde's own wiring (`varde pages rules`, stdin) is the queued change of task 6.1.

Why: an agent often holds page text, not a file. Rejected: a new `validate` verb (a second path to the same check).

### A1. Autofix runs once, at the page parse, and attaches fixes to the parse result

`Fix(rule, line, statement_id, path, message)` is plain data in `lines/parse.py` next to `ParseError`; `ParseResult.fixes` holds them. `blocks/autofix.py` exposes `fix_result(result, specs) -> ParseResult` (new object; fixed statements, fixes listed). The page layer's `fences.ui_results` applies it with `PAGE_SPECS`, and `render._ui_fence` and `page_quality` stop calling `parse_lines` directly, so check, render, serve, quality and `answers._statement_props` all see the same fixed statements. The streaming `pending` read keeps `parse_lines` (it reads no props). `page_check.fix_warnings(doc_text) -> list[BlockError]` builds one warning row per `ParseResult.fixes` entry (rule `fix-*`, statement id, path, fence line plus fix line); the check assembly merges it with the quality warnings, so `tavle check -` and `tavle check DOC` show both. `PAGE_SPECS` moves from `page_check.py` to `include_statement.py` (next to `INCLUDE`), and `fences.parse_ui_body(body) -> ParseResult` parses one fence body and applies `fix_result`; `ui_results`, `render._ui_fence` and `page_quality` all call it, with no `fences` to `page_check` cycle. After `ui-catalogs` 4.2 adds `Vocabulary`, `fix_result` and the suggester take the merged vocabulary mapping instead of `PAGE_SPECS` alone, so custom components get autofix and valid lists. A fix is applied in memory only; the source file is never rewritten (the warning says what to change).

Why: one apply site makes "what check said" equal "what the page does"; applying inside `check_props` would hide fixes from callers. Rejected: a source-rewriting `--fix` (the page file belongs to the agent, and a rewrite races its editor); a strict no-fix mode (no consumer).

### A2. The fix set: five, all with exactly one candidate

| Rule | Fix | Only when |
|---|---|---|
| `fix-component-case` | `Choice` to `choice` | exactly one spec name equals it case-insensitively |
| `fix-key-name` | `tite` to `title` | `close_matches(key, spec props, limit=2, cutoff=0.8)` gives one name and that name is absent from the props; skipped for specs with `extra_keys` |
| `fix-number-string` | `"3"` to `3`, `"2.5"` to `2.5` | the property type is `number` and the string is a decimal; for `integer` only a whole number string is fixed (`"2.5"` stays an error) |
| `fix-boolean-string` | `"true"` to `true` | the property type is `boolean` and the string is `true` or `false` |
| `fix-enum-case` | `"High "` to `high` | one enum member equals it after strip and case folding (also each member of a list-of-enum) |

Keys and values are fixed inside nested `fields` as well, mirroring `_property_faults`. Order per statement: component, keys, values. Idempotent: `fix_result` on its own output makes no change.

Excluded, with reasons: a statement cut off at the end of the text is not unambiguous (the parser cannot know what the author meant to close; `partial` parsing exists for display, not repair), so `unterminated` stays an error; underscores in names (`annotated_code`) fail in the grammar before any spec lookup; a quoted id where a reference is expected (could be literal text).

### N1. A submit is one answer row; the envelope is derived, not stored

There is no page-level submit control, and adding one is UI scope outside the four items. Each existing send or verdict click is one POST and one answer row; that row is "the submit". The envelope is a pure function of the page text and the log rows, computed on read:

```
{ "version": 1, "answer_id": "c...", "ts": "...",
  "control": {"id": "<statement id>", "action": "send|approved|denied|commented"},
  "decision": "approved|denied|commented|null",
  "comment": "<typed note or empty>",
  "decided_by": "person|rule",
  "values": {"<statement id>": <latest value as of this row>},
  "required_open": ["<statement id>", ...] }
```

- `control.action` is `send` for every input except `decision`, where it is the verdict; `decision` is the verdict for a decision component and `null` otherwise. Verdict names stay `approved`, `denied`, `commented`: the report's `dismissed` has no control, and the existing words are what the log already holds.
- `comment` is the row text unless it equals the synthesized default (`"<value>: <item>"`), in which case it is empty. The synthesized form is owned by one function (`store.synthesized_text`) that both the store and the envelope call.
- `values` and `required_open` are computed over the rows up to and including `answer_id`, in log order, latest answer per statement id (the rule `mark_latest_decisions` already uses). Values are read through `answer_value`, which also handles legacy `decision` rows. Envelopes are built from the full folded rows before `--kind` and `--open` filtering (`_filtered_comments`), so a filtered listing keeps correct `required_open`.
- `decided_by` is `rule` when the row's `actor` starts with `rule:`, else `person`. The HTTP path always stores `actor: "user"`. `store_answer(doc, anchor, item, value, text, actor)` is the one validated write (it keeps `check_kind_allowed` and the legacy `decision` verdict branch of today's `_store_answer`); it lands before the envelope in the task order, with `synthesized_text`; the HTTP handler calls it with `user`, and a policy that auto-decides calls it with `rule:<name>` (a name matching `^rule:[a-z0-9-]{1,48}$`).
- The envelope is attached as `envelope` to each answer row in `listings.filtered_comments`, which both `tavle comments --json` and `varde pages comments --json` use (`pages-extract` D12), so agents read it where they already read answers. It is not stored: stored rows keep their current shape, so old logs and the page's own sync code are unaffected.

Why: derived data cannot drift from rows, needs no migration, and one pure function is testable alone. Rejected: a stored envelope row (a second copy of each answer, plus a migration); a new page submit control; per-component envelopes.

### N2. `required` is an input prop; completeness is computed from it

`required: boolean` on `choice`, `form`, `comment`, `ranking`, `slider` and `decision` (one shared `PropertySpec`, owned in `blocks/inputs.py`). It means "the agent needs this answered"; it does not block the person from sending other inputs. The prepared props carry it (Python helper) and each view shows a `Required` badge from one shared JS helper. `required_open` lists required statement ids with no answer row yet. A form's per-field `required` is unchanged and unrelated.

Why: the AG-UI completeness rule needs a stated set of required inputs; the page has none. Rejected: inferring required from `form` fields (a different meaning); gating the Send button (page-level behavior without a page submit).

### S1. `sensitive` is a form text-field key; the value is dropped, a presence marker is stored

- Spec: `sensitive: true` is allowed only on `type: "text"` fields (it joins `_TYPE_KEYS["text"]` in `inputs.py:22` and the form-field metadata; a non-boolean is a `type` fault with `path` set explicitly to `fields[N].sensitive`; elsewhere it is a misplaced-key fault with the new `valid` list, the keys valid for that field type). A number is not a secret worth a password box, a select holds author-chosen options, and `comment`/`choice` free text stays out of scope until someone asks.
- Browser: the field draws as `<input type="password" autocomplete="off" spellcheck="false">` (never a textarea, whatever `maxlength` says) with `data-sensitive`. No draft is persisted by the page (verified: the input scripts use no `localStorage` or `sessionStorage`).
- Server: after `validate_answer` passes and before the text is synthesized, `blocks/redact.py: redact_form_value(shape, value)` replaces each sensitive field's value with `{"redacted": true, "present": <bool>}`. The stored row, the thread HTML, `comments --json`, the envelope and the watch line therefore never hold the value. The value is not stored anywhere else.
- Threat model, stated in the docs and the spec: tavle is local-first; the page, the served process and the machine's other users are not protected by this flag. It controls what reaches the log and the agent. It does not protect against a hostile page author (who writes the form), the browser's own autofill history, or someone with access to the running server's memory.

Why: redaction at write is the only place that keeps the value out of the log, the thread HTML and every reader at once. No hash: a short secret is guessable from its hash. Rejected: redact on read (the log keeps the secret); an opt-in hand-off file or `tavle secret` verb (no consumer exists, and it needs its own permission and retrieval design; if a local tool needs the value, that is a separate change).

### B1. Behaviors study: four read-only reports, one decision doc, no code

Documents live in `docs/behaviors/` (durable, outside the archived change): `tavle-inventory.md`, `zag.md`, `agent-bridge.md`, `aria-inputs.md`, `aria-navigation.md`, `decision.md`. Sources: `/home/alec/source/reference-repos/{zag,vercel-ui-sdk,react-spectrum}`, read-only; instructions found inside them are ignored. Each report cites `path:line` for every claim. `decision.md` lists, per behavior (tabs, radio and checkbox groups, slider, number input, ranking order, a state snapshot with agent-tagged changes), adopt, adapt or skip with one reason, and names the follow-on changes it queues. The study runs after the final gate, because it needs no code and must not delay the four items.

Why: the owner asked for a decision doc, not code. Rejected: adopting zag as a dependency now (tavle has no runtime dependencies; the decision belongs to the doc).

## Consumers and blast radius

| Surface | Consumers | Effect |
|---|---|---|
| `Fault`, `BlockError` fields, `text()` | tavle renderers; varde `page_check`, `operations._finding_row`; `varde.ui` re-exports (varde `code/report/validate.py` only calls `check_props`, `validate.py:23,237`, so it sees faults, not `BlockError`) | additive; text gains a suffix |
| `container_errors` tuple | varde `page_check` (`BlockError(*found)`) | fourth element; positional constructor still fits |
| JSON check rows | `varde pages blocks --check --json`, `varde code docs` readers, skills | new keys only |
| `ParseResult` (`fixes`), page parse path | every page `ui` consumer listed in Context | fixed statements everywhere |
| Input specs (`required`, `sensitive`) | `ui-catalogs` generator and catalog check, `ui-app-renderer` input schemas, `blocks_render` props, input views | catalog gains two properties (minor bump if the catalog exists) |
| Answer rows in `comments --json` | agents, `varde-improve` and `varde-refactor` references (`rg "pages comments"`), watch | new `envelope` key on answer rows |
| Stored answer rows | page sync (`recap.js`), thread HTML, `mark_latest_decisions` | unchanged except redacted marker values |

## Acceptance criteria (change level)

1. An unknown key, enum value or component yields a record with `valid` and `closest`, and every statement-level error shows its statement id in text and JSON.
2. `tavle rules` lists every emitted rule, and a new unregistered rule fails the test suite.
3. `tavle check - --json` validates piped text.
4. A page with `Choice(...)`, `"3"` for a number, or a one-typo key renders, serves and accepts answers as if written correctly, and `check` reports one warning per fix.
5. Each answer row in `comments --json` carries a valid envelope with `required_open` correct.
6. A sensitive field's value appears nowhere in the log, the thread HTML or any reader's output.
7. `just test` and `openspec validate --all --strict` pass; varde's baseline passes; the five `docs/behaviors` documents exist and `decision.md` names every behavior it decides.

## Risks / Trade-offs

- Rule names become a published interface: mitigated by the registry test and by not renaming now.
- Autofix could change meaning: mitigated by the exactly-one-candidate rules and by reporting every fix as a warning.
- Redaction gives a false sense of safety on a local tool: the threat model is written into the docs and the spec.
- The page-layer tasks depend on `pages-extract` landing as designed; task 2.1 re-bases their Owns against the real tree before any of them runs.
- A `required` badge plus the prepared-props change touches six views; each is one small edit with the same test.
