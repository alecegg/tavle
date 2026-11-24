"""Shared text and input size limits."""

import re

MAX_TEXT = 8000
MAX_ITEM = 600
# C0 and C1 controls (tab, newline, return allowed), NUL, bidi overrides and isolates.
CONTROLS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")
