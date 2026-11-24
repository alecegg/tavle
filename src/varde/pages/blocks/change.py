"""The shared change vocabulary: `change` and `was` on a row, field or entity."""

from varde.pages.blocks.rules import Fault
from varde.pages.blocks.spec import PropertySpec

CHANGES = ("added", "modified", "removed", "renamed")
_ALLOWED = ", ".join(CHANGES)
CHANGE_FIELDS = (
    "change  optional: added, modified, removed or renamed",
    "was     optional previous name, type or value; required for renamed only",
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


def change_faults(data: dict[str, object], where: str) -> list[Fault]:
    """All faults for the optional `change` and `was` keys of a table with no
    property metadata (`backend` until it declares them)."""
    faults: list[Fault] = []
    if "change" in data and data["change"] not in CHANGES:
        faults.append(Fault("change", f"{where}: change must be one of {_ALLOWED}"))
    was = data.get("was")
    if "was" in data and not (isinstance(was, str) and was.strip()):
        faults.append(Fault("type", f"{where}: 'was' must be a non-empty string"))
    return faults + change_rule_faults(data, where)
