"""Block type for asking the user to approve, deny or comment."""

from ..blocks.rules import Fault, duplicates
from ..blocks.spec import BlockSpec, PropertySpec

OPTIONS = ("approve", "deny", "comment")


def validate_decision(data: dict[str, object]) -> list[Fault]:
    options = data.get("options")
    if not isinstance(options, list):
        return []
    names = [o for o in options if isinstance(o, str) and o in OPTIONS]
    return [
        Fault("option-duplicate", f"decision.options: '{o}' is listed twice")
        for o in duplicates(names)
    ]


DECISION = BlockSpec(
    "decision",
    "A question the user answers with approve, deny or a comment",
    (
        "question: the text asked.",
        "options: default is all three of approve, deny and comment.",
        "evidence: rows of {label, text}; label is a short label.",
        "diff: shown preformatted.",
    ),
    r"""decision = decision(
  question: "Accept the shorter build-skill intro?",
  options: ["approve", "deny", "comment"],
  diff: "- Read the whole file first.\n+ Read the task file first.",
  evidence: [
    {"label": "friction", "text": "3 sessions skipped the intro"},
    {"label": "token delta", "text": "-120 tokens per run"},
  ],
)
""",
    validate_decision,
    block_type="decision",
    properties=(
        PropertySpec("question", "string", required=True, nonempty=True),
        PropertySpec("options", "list", items="string", enum=OPTIONS, nonempty=True),
        PropertySpec(
            "evidence",
            "list",
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("text", "string", required=True, nonempty=True),
            ),
        ),
        PropertySpec("diff", "string", nonempty=True),
    ),
)
