"""Check data/projects.json and data/publications.json against the frozen contract.

Mirrors the data contract in the architecture spec (site-pessoal-spec.md,
section 3.2 and 3.3), which the Astro site also validates with Zod. This is
the Python side of that same contract: change a rule here, not in the
render or the SVG code, so the two consumers cannot silently disagree.
"""

from __future__ import annotations

import re

from . import datastore

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TAGLINE_MAX_LENGTH = 110
LANGUAGES_MIN = 1
LANGUAGES_MAX = 4
VALID_PUBLICATION_STATUSES = {"published", "accepted", "submitted", "in preparation"}

REQUIRED_PROJECT_FIELDS = (
    "slug", "title", "tagline", "summary", "category", "languages",
    "year", "order", "pinned", "has_page", "headline_metric",
    "publications", "links",
)
REQUIRED_PUBLICATION_FIELDS = ("id", "year", "title", "venue", "status", "url", "doi")


def _errors_for_projects(projects: dict) -> list[str]:
    errors: list[str] = []
    seen_slugs: set[str] = set()
    for index, item in enumerate(projects.get("items", [])):
        label = f"projects.items[{index}]"
        missing = [field for field in REQUIRED_PROJECT_FIELDS if field not in item]
        if missing:
            errors.append(f"{label}: missing field(s) {missing}")
            continue
        slug = item["slug"]
        if not SLUG_PATTERN.match(slug):
            errors.append(f"{label}: slug '{slug}' does not match {SLUG_PATTERN.pattern}")
        if slug in seen_slugs:
            errors.append(f"{label}: duplicate slug '{slug}'")
        seen_slugs.add(slug)
        if len(item["tagline"]) > TAGLINE_MAX_LENGTH:
            errors.append(f"{label}: tagline longer than {TAGLINE_MAX_LENGTH} characters")
        language_count = len(item["languages"])
        if not (LANGUAGES_MIN <= language_count <= LANGUAGES_MAX):
            errors.append(
                f"{label}: languages must have {LANGUAGES_MIN}-{LANGUAGES_MAX} entries, "
                f"got {language_count}"
            )
        if not item["links"].get("repo"):
            errors.append(f"{label}: links.repo is required")
    return errors


def _errors_for_publications(publications: dict) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(publications.get("items", [])):
        label = f"publications.items[{index}]"
        missing = [field for field in REQUIRED_PUBLICATION_FIELDS if field not in item]
        if missing:
            errors.append(f"{label}: missing field(s) {missing}")
            continue
        publication_id = item["id"]
        if publication_id in seen_ids:
            errors.append(f"{label}: duplicate id '{publication_id}'")
        seen_ids.add(publication_id)
        if item["status"] not in VALID_PUBLICATION_STATUSES:
            errors.append(
                f"{label}: status '{item['status']}' not in {sorted(VALID_PUBLICATION_STATUSES)}"
            )
    return errors


def _errors_for_cross_references(projects: dict, publications: dict) -> list[str]:
    """Every id a project claims in `publications` must exist in publications.json."""
    errors: list[str] = []
    known_ids = {item["id"] for item in publications.get("items", []) if "id" in item}
    for index, item in enumerate(projects.get("items", [])):
        for publication_id in item.get("publications", []):
            if publication_id not in known_ids:
                errors.append(
                    f"projects.items[{index}] ('{item.get('slug')}'): "
                    f"publication id '{publication_id}' not found in publications.json"
                )
    return errors


def validate() -> list[str]:
    """Return human-readable errors; an empty list means the data is valid."""
    projects = datastore.load("projects.json")
    publications = datastore.load("publications.json")
    errors: list[str] = []
    errors.extend(_errors_for_projects(projects))
    errors.extend(_errors_for_publications(publications))
    errors.extend(_errors_for_cross_references(projects, publications))
    return errors
