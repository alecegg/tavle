"""Validate contrast and status colour separation in both schemes."""

import colorsys
from collections.abc import Mapping
from itertools import combinations
from typing import cast

from varde.base.contrast import RGBA, composite, contrast_ratio
from varde.pages.theme.derive_colour import derive_colour
from varde.pages.theme.tokens import ThemeError

STATUS = ("success", "warning", "danger", "info", "decision")
PAIRS = (
    *(
        (name, background, 4.5)
        for name in ("text", "text-secondary", "accent", "accent-alt")
        for background in ("surface", "card", "surface-sunk")
    ),
    ("on-accent", "accent", 4.5),
    *(
        (name, background, 4.5)
        for name in STATUS
        for background in ("surface", "card", f"{name}-tint")
    ),
    *((f"series-{i}", "card", 3.0) for i in range(1, 6)),
    *(("border-interactive", background, 3.0) for background in ("surface", "card")),
)


def validate_theme(
    light: Mapping[str, str],
    dark: Mapping[str, str],
    shared: Mapping[str, object],
    layer: str,
) -> None:
    """Raise one error containing every failed pair across both schemes."""
    failures: list[str] = []
    for scheme, tokens in (("light", light), ("dark", dark)):
        palette = derive_colour(
            tokens,
            float(str(shared["tint-strength"])),
            float(str(shared["border-strength"])),
        )

        def colour(name: str, palette: dict[str, RGBA | str] = palette) -> RGBA:
            key = {"card": "surface-elevated", "accent-alt": "accent-2"}.get(name, name)
            if name.endswith("-tint"):
                tint = palette["--vd-tone-" + name.replace("danger-", "risk-")]
                card = palette["--vd-surface-elevated"]
                return composite(cast("RGBA", tint), cast("RGBA", card))
            value = palette["--vd-" + key]
            return cast("RGBA", value)

        for tone in ("info", "decision", "risk", "warning", "success"):
            fg = colour(f"tone-{tone}-text")
            tint = cast("RGBA", palette[f"--vd-tone-{tone}-tint"])
            for background in ("surface", "card", "surface-sunk"):
                # Two tints: a tinted badge inside a tinted row.
                stacked = composite(tint, composite(tint, colour(background)))
                ratio = contrast_ratio(fg, stacked)
                if ratio < 4.5:
                    hex_value = "#" + "".join(f"{round(c):02x}" for c in fg[:3])
                    failures.append(
                        f"{layer}: [{scheme}] tone-{tone}-text {hex_value} on "
                        f"two tone-{tone}-tint layers over {background} "
                        f"is {ratio:.1f}:1, "
                        "needs 4.5:1"
                    )

        for foreground, background, required in PAIRS:
            fg = (
                colour(foreground)
                if foreground != "decision"
                else colour("tone-decision-text")
            )
            ratio = contrast_ratio(fg, colour(background))
            if ratio < required:
                hex_value = "#" + "".join(f"{round(c):02x}" for c in fg[:3])
                failures.append(
                    f"{layer}: [{scheme}] {foreground} {hex_value} on "
                    f"{background} is {ratio:.1f}:1, needs {required:.1f}:1"
                )
        for first, second in combinations(STATUS, 2):
            a = colorsys.rgb_to_hls(
                *(
                    c / 255
                    for c in colour(
                        "tone-" + first.replace("danger", "risk") + "-edge"
                    )[:3]
                )
            )
            b = colorsys.rgb_to_hls(
                *(
                    c / 255
                    for c in colour(
                        "tone-" + second.replace("danger", "risk") + "-edge"
                    )[:3]
                )
            )
            distance = min(abs(a[0] - b[0]), 1 - abs(a[0] - b[0])) * 360
            if a[2] >= 0.15 and b[2] >= 0.15 and distance < 20:
                failures.append(
                    f"{layer}: [{scheme}] {first} and {second} hues differ by "
                    f"{distance:.1f} degrees, need 20.0 degrees"
                )
    if failures:
        raise ThemeError("\n".join(failures))
