"""Component `decision`: the verdicts its answer accepts.

The block itself renders client-side (`static/components/decision.js`).
"""

from varde.ui.blocks.decision import OPTIONS
from varde.ui.blocks.spec import AnswerSchema
from varde.ui.blocks_render.common import as_list
from varde.ui.blocks_render.inputs import choice_values

VERDICT_OF = {"approve": "approved", "deny": "denied", "comment": "commented"}
LABELS = {"approve": "Approve", "deny": "Deny", "comment": "Comment"}


def decision_as_choice(data: dict[str, object]) -> dict[str, object]:
    """The `choice` props a decision stands for: one option per verdict, a note box."""
    options = [
        o for o in as_list(data.get("options", list(OPTIONS))) if o in VERDICT_OF
    ]
    return {
        "question": data.get("question", ""),
        "options": [{"label": LABELS[o], "value": VERDICT_OF[o]} for o in options],
        "comment": "comment" in options,
    }


def decision_answer_schema(data: dict[str, object]) -> AnswerSchema:
    """A decision answers like a choice of verdicts; `commented` needs text."""
    allowed = choice_values(decision_as_choice(data))
    return AnswerSchema("verdict", ("text",), allowed)
