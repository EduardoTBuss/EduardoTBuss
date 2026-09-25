"""Draw the two-file GitHub stats strip embedded in the README via <picture>.

Only the constants below control layout and palette -- change the accent
color, the font stack or the field order here, nowhere else.

Design decision (documented, not silent): `stats-light.svg` and
`stats-dark.svg` render byte-identical content. The spec's real guarantee
against GitHub's light/dark split is a transparent background plus a single
neutral color legible on both themes (`#7d8590`, ~4.6:1 on white and ~4.9:1
on #0d1117); `<picture>` swapping the *file* is explicitly "an improvement,
not the defense" (spec 7.4). Making the two files diverge in tone would
break the guarantee for exactly the reader it protects: a client that shows
`stats-light.svg` (the <img> fallback) over a dark page background because
it ignores <picture> entirely. Two files still exist, so <picture> keeps
working for clients that do support it, and the markup is ready for a
future tone refinement without touching this module's structure.
"""

from __future__ import annotations

import html
from typing import NamedTuple

from . import paths

# --- Layout ---------------------------------------------------------------
VIEW_WIDTH = 760
VIEW_HEIGHT = 44
PADDING_X = 12
BASELINE_Y = 27
FONT_STACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
# Largest candidate that keeps the text inside the content width wins; this
# adapts automatically if a future field makes the line longer, instead of
# needing a hand-tuned font size again.
CANDIDATE_FONT_SIZES = (13, 12, 11, 10, 9)
GLYPH_WIDTH_FACTOR = 0.6  # empirical average glyph advance for ui-monospace, in em

# --- Palette (single source of truth) --------------------------------------
TEXT_COLOR = "#7d8590"
LABEL_WEIGHT = 400
VALUE_WEIGHT = 700

SEPARATOR = " · "  # middle dot
TOP_LANGUAGES_SHOWN = 3


class Segment(NamedTuple):
    text: str
    weight: int


def _segments(stats: dict) -> list[Segment]:
    """Ordered (text, weight) pairs; weight distinguishes label vs. value.

    Field order and inclusion rules follow spec 7.3: `following` is left
    out (says nothing about the work), `forks_received` only appears when
    greater than zero, and `top_languages` shows only the top 3 by
    repository count, name only, no proportion bar.
    """
    segments: list[Segment] = [
        Segment(str(stats.get("public_repos", "?")), VALUE_WEIGHT),
        Segment(" repositories", LABEL_WEIGHT),
        Segment(SEPARATOR, LABEL_WEIGHT),
        Segment(str(stats.get("stars_received", "?")), VALUE_WEIGHT),
        Segment(" stars", LABEL_WEIGHT),
        Segment(SEPARATOR, LABEL_WEIGHT),
        Segment(str(stats.get("followers", "?")), VALUE_WEIGHT),
        Segment(" followers", LABEL_WEIGHT),
    ]

    languages = [entry["name"] for entry in stats.get("top_languages", [])[:TOP_LANGUAGES_SHOWN]]
    if languages:
        segments.append(Segment(SEPARATOR, LABEL_WEIGHT))
        segments.append(Segment(", ".join(languages), VALUE_WEIGHT))

    forks = stats.get("forks_received", 0)
    if forks:
        segments.append(Segment(SEPARATOR, LABEL_WEIGHT))
        segments.append(Segment(str(forks), VALUE_WEIGHT))
        segments.append(Segment(" forks", LABEL_WEIGHT))

    active_since = stats.get("account_created_year")
    if active_since:
        segments.append(Segment(SEPARATOR, LABEL_WEIGHT))
        segments.append(Segment("active since ", LABEL_WEIGHT))
        segments.append(Segment(str(active_since), VALUE_WEIGHT))

    refreshed_at = str(stats.get("refreshed_at") or "")
    if refreshed_at:
        segments.append(Segment(SEPARATOR, LABEL_WEIGHT))
        segments.append(Segment(f"updated {refreshed_at[:10]}", LABEL_WEIGHT))

    return segments


def build_summary_line(stats: dict) -> str:
    """Plain-text strip content, reused as the README <img alt="">.

    Building it from the same segments as the SVG is what keeps the alt
    text and the visible strip from drifting apart (spec 7.4).
    """
    return "".join(segment.text for segment in _segments(stats))


def _pick_font_size(text_length: int) -> int:
    content_width = VIEW_WIDTH - 2 * PADDING_X
    for size in CANDIDATE_FONT_SIZES:
        if text_length * size * GLYPH_WIDTH_FACTOR <= content_width:
            return size
    return CANDIDATE_FONT_SIZES[-1]


def render(stats: dict) -> str:
    """Render the stats strip SVG markup (no <style>, no webfont, no animation)."""
    segments = _segments(stats)
    font_size = _pick_font_size(sum(len(segment.text) for segment in segments))
    tspans = "".join(
        f'<tspan font-weight="{segment.weight}">{html.escape(segment.text, quote=True)}</tspan>'
        for segment in segments
    )
    title = html.escape(build_summary_line(stats), quote=True)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" '
        f'viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" role="img" aria-labelledby="stats-title">\n'
        f'  <title id="stats-title">{title}</title>\n'
        f'  <text x="{PADDING_X}" y="{BASELINE_Y}" fill="{TEXT_COLOR}" '
        f'font-family="{FONT_STACK}" font-size="{font_size}">{tspans}</text>\n'
        f'</svg>\n'
    )


def write(stats: dict) -> None:
    """Write generated/stats-light.svg and generated/stats-dark.svg."""
    content = render(stats)
    paths.write_generated("stats-light.svg", content)
    paths.write_generated("stats-dark.svg", content)
