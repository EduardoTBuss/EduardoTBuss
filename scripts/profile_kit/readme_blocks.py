"""Render the three generated blocks of README.md between HTML markers.

Everything outside a marker pair is hand-written prose and is never
touched. Change the projects table's columns, the publication citation
format, or the stats caption here -- each is a change in one function of
this one file, never in generate_visuals.py.
"""

from __future__ import annotations

from . import datastore, paths, stats_band

SITE_BASE_URL = "https://eduardotbuss.github.io"
PUBLICATIONS_SHOWN = 3
STATS_CAPTION = "_Updated daily._"

# (marker key) -> (opening comment, closing comment). Both must already
# exist in README.md; render_readme() refuses to write if either is missing,
# so a typo'd marker fails loudly instead of silently corrupting the file.
MARKERS: dict[str, tuple[str, str]] = {
    "projects": ("<!-- projects:start -->", "<!-- projects:end -->"),
    "publications": ("<!-- publications:start -->", "<!-- publications:end -->"),
    "stats": ("<!-- stats:start -->", "<!-- stats:end -->"),
}


def _escape_cell(value: object) -> str:
    """Escape characters that would break a Markdown table cell or line."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_projects_table(projects: dict) -> str:
    """`Project | What it is | Stack`, pinned only, sorted by manual order.

    Project links point at the site's project page, not at GitHub -- the
    site is the destination, the README is the shortcut (spec 7.1).
    """
    pinned = sorted(
        (item for item in projects["items"] if item.get("pinned")),
        key=lambda item: item["order"],
    )
    rows = ["| Project | What it is | Stack |", "|---|---|---|"]
    for item in pinned:
        url = f"{SITE_BASE_URL}/projects/{item['slug']}/"
        title = _escape_cell(item["title"])
        tagline = _escape_cell(item["tagline"])
        stack = _escape_cell(", ".join(item["languages"]))
        rows.append(f"| [{title}]({url}) | {tagline} | {stack} |")
    return "\n".join(rows)


def _publication_link(item: dict) -> str:
    url = item.get("url") or ""
    doi = item.get("doi") or ""
    target = url or (f"https://doi.org/{doi}" if doi else "")
    return f" [DOI]({target})" if target else ""


def _publication_line(item: dict) -> str:
    status = item.get("status", "published")
    status_suffix = f" ({status})" if status != "published" else ""
    citation = f"{item['title']}. {item['venue']}, {item['year']}{status_suffix}."
    return f"- {citation}{_publication_link(item)}"


def render_publications_list(publications: dict) -> str:
    """Three most recent publications, newest year first.

    Ties break by file order: Python's sort is stable, and `reverse=True`
    keeps that stability, so two items sharing a year keep the order the
    author gave them in data/publications.json (spec 7.1).
    """
    ordered = sorted(publications["items"], key=lambda item: item["year"], reverse=True)
    return "\n".join(_publication_line(item) for item in ordered[:PUBLICATIONS_SHOWN])


def render_stats_block(github_stats: dict) -> str:
    """<picture> pointing at the two generated SVGs, alt text built from the same data."""
    alt = _escape_cell(stats_band.build_summary_line(github_stats))
    lines = [
        "<picture>",
        '  <source media="(prefers-color-scheme: dark)" srcset="./generated/stats-dark.svg">',
        f'  <img src="./generated/stats-light.svg" width="{stats_band.VIEW_WIDTH}" alt="{alt}">',
        "</picture>",
        "",
        STATS_CAPTION,
    ]
    return "\n".join(lines)


def _replace_block(text: str, key: str, content: str) -> str:
    start_marker, end_marker = MARKERS[key]
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"README.md is missing the '{key}' markers ({start_marker} / {end_marker}); "
            "aborting without writing anything."
        )
    body_start = start + len(start_marker)
    return text[:body_start] + "\n" + content + "\n" + text[end:]


def render_readme() -> None:
    """Rewrite only the generated blocks of README.md; idempotent by construction."""
    text = paths.README.read_text(encoding="utf-8")
    projects = datastore.load("projects.json")
    publications = datastore.load("publications.json")
    github_stats = datastore.load("github.json")

    text = _replace_block(text, "projects", render_projects_table(projects))
    text = _replace_block(text, "publications", render_publications_list(publications))
    text = _replace_block(text, "stats", render_stats_block(github_stats))

    paths.write_text_artifact(paths.README, text)
