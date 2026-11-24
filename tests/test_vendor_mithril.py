"""The vendored Mithril file matches the version, licence and hash recorded in docs."""

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VENDORED = REPO / "src/tavle/static/vendor/mithril.js"
LICENCES = REPO / "docs/third-party-licences.md"
ROW = re.compile(
    r"^\| `([^`]+mithril\.js)` \| (\S+) \| (\S+) \| `([0-9a-f]{64})` \|$",
    re.MULTILINE,
)


def test_vendored_mithril_hash_matches_recorded_row() -> None:
    match = ROW.search(LICENCES.read_text(encoding="utf-8"))
    assert match, "no vendored mithril row in docs/third-party-licences.md"
    path, version, licence, recorded = match.groups()
    assert REPO / path == VENDORED
    assert hashlib.sha256(VENDORED.read_bytes()).hexdigest() == recorded
    assert (version, licence) == ("2.3.8", "MIT")


def test_header_names_the_recorded_version_and_licence() -> None:
    header = VENDORED.read_text(encoding="utf-8").splitlines()[0]
    assert "mithril 2.3.8" in header and "MIT" in header


def test_licence_file_ships_beside_the_vendored_file() -> None:
    licence = VENDORED.with_name("mithril.LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in licence and "Leo Horie" in licence
