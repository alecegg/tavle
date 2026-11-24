"""The shared change vocabulary: `change` and `was` on a row, field or entity."""

from varde.ui.blocks.rules import Fault
from varde.ui.blocks.spec import PropertySpec

CHANGES = ("added", "modified", "removed", "renamed")
_ALLOWED = ", ".join(CHANGES)
CHANGE_NOTES = (
    "change: added, modified, removed or renamed.",
    "was: the previous name, type or value; required for renamed only.",
)


# The metadata of `change` and `was`, for every table that carries them.
CHANGE_PROPERTIES = (
    PropertySpec("change", "string", enum=CHANGES),
    PropertySpec("was", "string", nonempty=True),
)


def change_rule_faults(data: dict[str, object], where: str) -> list[Fault]:
    """Cross-field rules of `change` and `was`; the properties own the rest."""
    faults: list[Fault] = []
    change = data.get("change")
    has_was = "was" in data
    if has_was and "change" not in data:
        faults.append(Fault("change", f"{where}: was needs a change ({_ALLOWED})"))
    if change == "renamed" and not has_was:
        faults.append(
            Fault("change", f"{where}: renamed needs was (the previous name)")
        )
    if change in ("added", "removed") and has_was:
        faults.append(Fault("change", f"{where}: {change} cannot have was"))
    return faults
