"""Draw the two-file GitHub stats card embedded in the README via <picture>.

Only the constants below control layout and palette -- change the accent
color, the font stack or the metric order here, nowhere else.

The card has two rows: four headline numbers, then a language bar. The
numbers are the API's own counts, and languages are counted per repository,
not per byte, which is why the bar is labelled that way.

Design decision (documented, not silent): `stats-light.svg` and
`stats-dark.svg` render byte-identical content. The real guarantee against
GitHub's light/dark split is a transparent background plus colors legible on
both themes (labels `#7d8590`, ~4.6:1 on white and ~4.9:1 on #0d1117, numbers
`#2f81f7` at a large bold size); `<picture>` swapping the *file* is "an
improvement, not the defense". Making the two files diverge in tone would break
the guarantee for a client that shows `stats-light.svg` (the <img> fallback)
over a dark page because it ignores <picture> entirely.

Nothing here depends on the date: the same data always renders the same bytes,
so the daily workflow has nothing to commit until a number actually changes.
"""

from __future__ import annotations

import html

from . import paths

# --- Layout ---------------------------------------------------------------
VIEW_WIDTH = 760
VIEW_HEIGHT = 124
PADDING_X = 12
COLUMN_WIDTH = (VIEW_WIDTH - 2 * PADDING_X) // 4
NUMBER_Y = 34
LABEL_Y = 54
BAR_TITLE_Y = 82
BAR_Y = 90
BAR_HEIGHT = 8
LEGEND_Y = 116
FONT_STACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
LEGEND_FONT_SIZE = 11
GLYPH_WIDTH_FACTOR = 0.6  # empirical average glyph advance for ui-monospace, in em
LEGEND_GAP = 18

# --- Palette (single source of truth) --------------------------------------
NUMBER_COLOR = "#2f81f7"
LABEL_COLOR = "#7d8590"
FALLBACK_LANGUAGE_COLOR = "#8b949e"
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "C": "#8a8a8a",
    "C++": "#f34b7d",
    "Java": "#b07219",
    "Jupyter Notebook": "#DA5B0B",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Astro": "#ff5a03",
    "VHDL": "#adb2cb",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
}

SEPARATOR = " · "  # middle dot
LANGUAGES_SHOWN = 6


def _metrics(stats: dict) -> list[tuple[str, str]]:
    """(number, label) pairs in display order.

    `following` is left out (it says nothing about the work) and so is any
    "updated" date (it would change every day and nothing else would).
    """
    since = stats.get("account_created_year")
    return [
        (str(stats.get("public_repos", "?")), "repositories"),
        (str(stats.get("stars_received", "?")), "stars received"),
        (str(stats.get("followers", "?")), "followers"),
        (str(since) if since else "?", "on GitHub since"),
    ]


def _languages(stats: dict) -> list[tuple[str, int]]:
    entries = stats.get("top_languages", [])[:LANGUAGES_SHOWN]
    return [(entry["name"], int(entry["repositories"])) for entry in entries]


def build_summary_line(stats: dict) -> str:
    """Plain-text card content, reused as the README <img alt="">.

    Built from the same data as the SVG so the alt text and the visible
    card cannot drift apart.
    """
    parts = [
        f"{label} {number}" if label.endswith("since") else f"{number} {label}"
        for number, label in _metrics(stats)
    ]
    languages = [name for name, _ in _languages(stats)[:3]]
    if languages:
        parts.append(", ".join(languages))
    return SEPARATOR.join(parts)


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _metric_nodes(stats: dict) -> list[str]:
    nodes = []
    for index, (number, label) in enumerate(_metrics(stats)):
        x = PADDING_X + index * COLUMN_WIDTH
        nodes.append(
            f'  <text x="{x}" y="{NUMBER_Y}" fill="{NUMBER_COLOR}" font-family="{FONT_STACK}" '
            f'font-size="28" font-weight="700">{_escape(number)}</text>'
        )
        nodes.append(
            f'  <text x="{x}" y="{LABEL_Y}" fill="{LABEL_COLOR}" font-family="{FONT_STACK}" '
            f'font-size="12">{_escape(label)}</text>'
        )
    return nodes


def _language_nodes(stats: dict) -> list[str]:
    languages = _languages(stats)
    if not languages:
        return []
    total = sum(count for _, count in languages) or 1
    content_width = VIEW_WIDTH - 2 * PADDING_X
    nodes = [
        f'  <text x="{PADDING_X}" y="{BAR_TITLE_Y}" fill="{LABEL_COLOR}" font-family="{FONT_STACK}" '
        f'font-size="11">languages, by repository</text>',
        f'  <clipPath id="bar"><rect x="{PADDING_X}" y="{BAR_Y}" width="{content_width}" '
        f'height="{BAR_HEIGHT}" rx="{BAR_HEIGHT // 2}"/></clipPath>',
        '  <g clip-path="url(#bar)">',
    ]
    cursor = float(PADDING_X)
    for name, count in languages:
        width = content_width * count / total
        color = LANGUAGE_COLORS.get(name, FALLBACK_LANGUAGE_COLOR)
        nodes.append(
            f'    <rect x="{cursor:.1f}" y="{BAR_Y}" width="{width:.1f}" height="{BAR_HEIGHT}" fill="{color}"/>'
        )
        cursor += width
    nodes.append("  </g>")

    legend_x = float(PADDING_X)
    for name, count in languages:
        color = LANGUAGE_COLORS.get(name, FALLBACK_LANGUAGE_COLOR)
        label = f"{name} {count}"
        nodes.append(f'  <circle cx="{legend_x + 4:.1f}" cy="{LEGEND_Y - 4}" r="4" fill="{color}"/>')
        nodes.append(
            f'  <text x="{legend_x + 14:.1f}" y="{LEGEND_Y}" fill="{LABEL_COLOR}" '
            f'font-family="{FONT_STACK}" font-size="{LEGEND_FONT_SIZE}">{_escape(label)}</text>'
        )
        legend_x += 14 + len(label) * LEGEND_FONT_SIZE * GLYPH_WIDTH_FACTOR + LEGEND_GAP
    return nodes


def render(stats: dict) -> str:
    """Render the stats card SVG markup (no <style>, no webfont, no animation)."""
    title = _escape(build_summary_line(stats))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_WIDTH}" height="{VIEW_HEIGHT}" '
        f'viewBox="0 0 {VIEW_WIDTH} {VIEW_HEIGHT}" role="img" aria-labelledby="stats-title">',
        f'  <title id="stats-title">{title}</title>',
        *_metric_nodes(stats),
        *_language_nodes(stats),
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def write(stats: dict) -> None:
    """Write generated/stats-light.svg and generated/stats-dark.svg."""
    content = render(stats)
    paths.write_generated("stats-light.svg", content)
    paths.write_generated("stats-dark.svg", content)
