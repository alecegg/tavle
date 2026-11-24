# Proposal

## Why

An agent that writes tavle pages and reads the answers back needs feedback it can act on without a human. The research ranking (`~/source/agent-memory/general/research/agent-ui-tools/report.md`, items 1 to 4) found four gaps in tavle (read at `d230167`) and varde (`aa398018`): some errors lack the statement id, `unknown-key` and enum faults do not list valid options, rule names are scattered literals, trivial slips cost a round trip, answers are one row per input with no completeness or origin record, and a secret typed into a form lands in the comment log in clear text.

## What Changes

- Errors an agent can act on: every statement-level error carries line and statement id (text and JSON); unknown-key, wrong-enum and unknown-component faults list valid options and the closest match; the rule names are one published registry (`RULES`, `tavle rules`); `tavle check -` validates text from stdin and prints JSON.
- Automatic fixes for unambiguous slips (component name case, one close-match key, numeric and boolean strings, enum case), applied at the single page parse and reported as `fix-*` warnings, so check, render, serve and answers see the same fixed statements.
- A typed answer envelope derived per answer row: control fired, values by statement id, decision, comment, decided by person or rule, required inputs still open. It is attached to the answer rows of `comments --json`. Input components gain a `required` prop.
- A `sensitive` flag on `form` text fields: the browser draws a password field and the server stores a presence marker instead of the value, so the value never reaches the log, the thread HTML or the agent.
- Later phase: a "behaviors" study of tavle's input and keyboard handling against `zag`, `vercel-ui-sdk` and `react-spectrum`, ending in a decision document (no code).
- Queued, not in this change: the varde side (`varde pages rules`, stdin check, skill text) as a separate varde change drafted by task 6.1.

Out of scope, with reasons in design.md: item 5 (generated agent reference; owned by `ui-catalogs`), repairing a statement cut off mid-stream (not unambiguous), renaming existing rules (breaking), a value hand-off path for sensitive fields (no consumer), a dismiss control.

## Capabilities

### New Capabilities

- `agent-errors`: error records, statement ids, valid options and closest match, the rule registry, the stdin validate entry.
- `agent-autofix`: the fixes, where they apply, how they are reported.
- `answer-envelope`: the envelope record, the `required` prop, rule-decided answers.
- `sensitive-fields`: the `sensitive` form field flag and its redaction.

### Modified Capabilities

(none; `openspec/specs` is empty)

## Impact

- tavle (`~/source/tavle`): `src/tavle/{suggest,rule_names}.py`, `lines/parse.py`, `blocks/{check,rules,inputs,inputs_ordered,decision,containers,redact}.py`, new `blocks/autofix*.py`, `blocks_render/{__init__,inputs,inputs_ordered}.py`, `static/components/{shared,choice,comment,ranking,slider,form,decision}.js`, theme `layers.py` (uses the shared suggester). After `pages-extract` 5.2: `page/{fences,render,page_quality,page_check,include,select}.py`, `comments/{envelope,store}.py`, `listings.py`, `cli.py`, `__init__.py`.
- Consumers: varde reaches tavle through `src/varde/ui.py` (editable path dependency); `varde pages blocks --check --json` rows (`operations._finding_row`, then `listings.finding_row`) gain fields additively; `code/report/validate.py` calls `check_props` and keeps working. `ui-catalogs` generates the catalog from the specs, so the new `required` and `sensitive` properties add catalog properties (additive minor bump when `just catalog-check` exists).
- Ordering: the change is queued after `pages-extract`. Groups 1 and 3.1 to 3.3, 4.1 to 4.4 and 5.1 to 5.3 are tavle-only and touch no path `pages-extract` owns (it adds `page/`, `comments/`, `serve/`, `cli.py` and edits `__init__.py`, README and `justfile`), so they may start earlier; every task marked `after: pages-extract 5.2` needs the moved code.
