"""Props for the image block: a `<figure>` with a lazy `<img>`, caption and description.

The server checks the file (`media`) and sends how it shows;
`static/components/image.js` builds the figure. Width and height come from the file
header so the layout never shifts. The picture links to the file; `static/image.js`
adds a zoom dialog. The `vb-alt` line repeats the alt text as plain text for readers
without the picture. A refused image stays an error card built here.
"""

from urllib.parse import quote

from ..blocks_render.common import card, esc
from ..media import Media

NOT_EMBEDDED = "Image not embedded in this export."
OPEN_LABEL = "Open image full size"
UNRESOLVED = "Image not shown: this page cannot read the file here."


def copy_text(data: dict[str, object]) -> str:
    return "\n".join(str(data[key]) for key in ("alt", "caption") if key in data)


def media_url(src: str) -> str:
    return "/media/" + quote(src)


def _picture(
    data: dict[str, object], media: Media, *, export: bool
) -> dict[str, object]:
    """How the file shows: an inline data URL (export), a link to it, or a note."""
    size = {"width": str(media.width), "height": str(media.height)}
    if export and not media.data_url:
        return {"kind": "missing", "note": NOT_EMBEDDED}
    if export:
        return {"kind": "inline", "src": media.data_url, **size}
    alt = str(data["alt"])
    label = f"{alt} (open full size)" if alt.strip() else OPEN_LABEL
    href = media_url(media.src)
    return {"kind": "link", "src": href, "href": href, "label": label, **size}


def image_props(
    data: dict[str, object], media: Media | None = None, *, export: bool = False
) -> dict[str, object]:
    """Props for the figure; without `media` (an included part) it is a note."""
    picture: dict[str, object] = {"kind": "missing", "note": UNRESOLVED}
    summary = f"Image: {data['alt']}"
    if media is not None:
        picture = _picture(data, media, export=export)
        summary = f"Image: {data['alt']} ({media.width} x {media.height} px)"
    return {
        "alt": str(data["alt"]),
        "caption": str(data["caption"]) if data.get("caption") else "",
        "narrow": data.get("width") == "narrow",
        "picture": picture,
        "summary": summary,
        "copy": copy_text(data),
    }


def render_refused(props: dict[str, object], reasons: list[str]) -> str:
    """The error card for an image that cannot be shown, with a text alternative."""
    items = "".join(f"<li>{esc(reason)}</li>" for reason in reasons)
    alt = str(props.get("alt") or "").strip() or "no description given"
    count = f"image block has {len(reasons)} error{'s' * (len(reasons) != 1)}"
    return (
        '<div class="vb">'
        + card(esc(count), f"<ul>{items}</ul>", "vb-error")
        + f'<p class="vb-alt">Image unavailable: {esc(alt)}</p></div>'
    )
