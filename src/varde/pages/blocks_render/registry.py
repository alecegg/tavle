"""One registry entry per component: spec (validate), props, answer schema.

`blocks.COMPONENT_SPECS` holds the specs; this module joins each with the
props hook that prepares validated props for the browser, where
`static/components/<name>.js` draws the block. `pages blocks` reads the specs and
line examples; the page renderer reads `props`; the answer path reads
`answer_schema`. `include` is the one statement with no component: the page
renderer expands it to the parts it names (`PAGE_STATEMENTS`).

Deviations from OpenUI Lang and its React component props (checked against
`packages/react-ui/src/genui-lib/<Component>/schema.ts`, shallow clone
2026-11-03). The line syntax itself is compatible: `id = Component(prop: value)`
with JSON-like values and references to earlier ids. Props are not.

- Props stay as the existing typed blocks define them, so stored output is
  unchanged: `table` takes `columns` and `rows` (OpenUI `Table` takes `Col(label,
  data)` children); `chart` takes `kind`, `labels` and `series` (OpenUI has one
  component per chart kind with `Series`/`Point` children); `decision`, `recap`
  and `deps` have no OpenUI counterpart.
- Prop names are the existing block keys; an OpenUI prop name is not accepted
  as an alias.
- Component names are the block names (`data-model`, `ui-states`), lower-case
  with hyphens; OpenUI names are PascalCase.
- No `$state`, `reactive()` props, `rules`, `Query`, `Mutation` or `@` actions;
  an answer is one validated row per input component (`AnswerSchema`), never an
  action. OpenUI `Slider` (`name`, `variant`, `min`, `max`, `step`,
  `defaultValue`, `value: number[]`) and `Form`/`RadioGroup` props are not
  adopted yet; `im-widgets-*` decide each input's props and record deviations
  here. `choice` takes `question`, `options` (strings or `label`/`detail`/
  `value` tables), `multiple` and `comment` (OpenUI `RadioGroup`/`CheckBoxGroup`
  are two components with `items`); `form` takes `fields` tables (OpenUI nests
  `FormControl` children) and answers one object; `comment` takes `label`.
  `decision` stays a typed block with its own markup; its "choice preset" is
  schema-only (`decision_as_choice` feeds the answer schema, nothing renders it).
  `ranking` takes `question` and `items` (the `choice` option shapes) and
  answers the values in ranked order; `slider` takes `label`, `min`, `max`,
  `step` (default 1) and `labels` (two end texts) and answers one number on a
  step. OpenUI `Slider` has `defaultValue` and a `number[]` value for ranges;
  neither is adopted (a slider has no preset answer, so a send needs a move).
"""

from collections.abc import Callable
from dataclasses import dataclass

from varde.pages.blocks import COMPONENT_SPECS
from varde.pages.blocks.spec import AnswerSchema, BlockSpec
from varde.pages.blocks_render.annotated_code import annotated_props
from varde.pages.blocks_render.backend import data_model_props, endpoint_props
from varde.pages.blocks_render.change_summary import change_summary_props
from varde.pages.blocks_render.charts import chart_props
from varde.pages.blocks_render.code import code_block_props
from varde.pages.blocks_render.common import as_dict
from varde.pages.blocks_render.containers import container_props
from varde.pages.blocks_render.decision import decision_answer_schema
from varde.pages.blocks_render.diagrams import diagram_props
from varde.pages.blocks_render.diff import diff_props
from varde.pages.blocks_render.file_tree import file_tree_props
from varde.pages.blocks_render.flow import flow_props
from varde.pages.blocks_render.image import image_props
from varde.pages.blocks_render.inputs import (
    choice_answer_schema,
    choice_props,
    comment_answer_schema,
    comment_props,
    form_answer_schema,
    form_props,
)
from varde.pages.blocks_render.inputs_ordered import (
    ranking_answer_schema,
    ranking_props,
    slider_answer_schema,
    slider_props,
)
from varde.pages.blocks_render.screen_flow import screen_flow_props
from varde.pages.blocks_render.screens import ui_states_props, wireframe_props
from varde.pages.blocks_render.sequence import sequence_props
from varde.pages.blocks_render.state import state_props
from varde.pages.graph import deps_layout

Props = dict[str, object]


PAGE_STATEMENTS = frozenset({"include"})


@dataclass(frozen=True)
class Component:
    spec: BlockSpec
    answer_schema: Callable[[Props], AnswerSchema | None] | None = None
    # Maps validated props to the props the browser draws from (default: as written).
    props: Callable[[Props], Props] | None = None


_PROPS: dict[str, Callable[[Props], Props]] = {
    "code": code_block_props,
    "annotated-code": annotated_props,
    "file-tree": file_tree_props,
    "diff": diff_props,
    "chart": chart_props,
    "diagram": diagram_props,
    "flow": flow_props,
    "state": state_props,
    "sequence": sequence_props,
    "screen-flow": screen_flow_props,
    "image": image_props,
    "wireframe": wireframe_props,
    "ui-states": ui_states_props,
    "change-summary": change_summary_props,
    "choice": choice_props,
    "form": form_props,
    "comment": comment_props,
    "ranking": ranking_props,
    "slider": slider_props,
    "deps": lambda props: deps_layout(as_dict(props.get("edges"))),
    "data-model": data_model_props,
    "endpoint": endpoint_props,
    "tabs": lambda props: container_props("tabs", props),
    "columns": lambda props: container_props("columns", props),
}
_ANSWER: dict[str, Callable[[Props], AnswerSchema | None]] = {
    "decision": decision_answer_schema,
    "choice": choice_answer_schema,
    "form": form_answer_schema,
    "comment": comment_answer_schema,
    "ranking": ranking_answer_schema,
    "slider": slider_answer_schema,
}

COMPONENTS: dict[str, Component] = {
    name: Component(spec, _ANSWER.get(name), _PROPS.get(name))
    for name, spec in COMPONENT_SPECS.items()
}
