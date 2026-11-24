"""Block type for settled notes: callout."""

from varde.pages.blocks.rules import Fault
from varde.pages.blocks.spec import BlockSpec, PropertySpec

TONES = ("info", "decision", "risk", "warning", "success")


def validate_callout(data: dict[str, object]) -> list[Fault]:
    return []


CALLOUT = BlockSpec(
    "callout",
    "A tinted note with a tone, a label and plain text",
    (
        "tone: the label shows its word.",
        "title: short heading.",
        "text: plain text; a blank line starts a paragraph, `code` marks inline code.",
    ),
    r"""callout = callout(
  tone: "decision",
  title: "Storage",
  text: "Use SQLite for the `queue` table; one writer is enough.",
)
""",
    validate_callout,
    properties=(
        PropertySpec("tone", "string", required=True, enum=TONES),
        PropertySpec("text", "string", required=True, nonempty=True),
        PropertySpec("title", "string", nonempty=True),
    ),
)
