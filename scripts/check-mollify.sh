#!/usr/bin/env bash
# Fail on mollify findings that are new against .mollify-baseline.json.
# Usage: check-mollify.sh [project-root]
# Mollify silently falls back to its defaults when .mollifyrc.json is broken, so check the file first.
set -euo pipefail

root="${1:-.}"
config="$root/.mollifyrc.json"

if ! python3 - "$config" 2>/dev/null <<'PY'
import json, sys

config = json.load(open(sys.argv[1]))
ceilings = (config.get("max_cyclomatic"), config.get("max_cognitive"))
gated = config.get("severity", {}).get("high-complexity") == "error"
sys.exit(not (all(isinstance(c, int) for c in ceilings) and gated))
PY
then
    echo "mollify config error: $config is missing, malformed or lacks integer ceilings or the high-complexity error severity" >&2
    exit 2
fi

uv run --locked mollify audit --path "$root" --baseline "$root/.mollify-baseline.json" --fail-on-regression
