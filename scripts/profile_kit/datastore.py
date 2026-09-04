"""Load and save the JSON data contract.

Single place that turns a filename into a `data/<name>` path and back into
Python objects. Every other module reaches the JSON files through here, so
switching the storage format (e.g. reading from a database instead of files)
is a one-file change.
"""

from __future__ import annotations

import json
from typing import Any

from . import paths


def load(name: str) -> Any:
    """Read and parse one file from data/ by name, e.g. load("projects.json")."""
    return json.loads((paths.DATA / name).read_text(encoding="utf-8"))


def save_json(name: str, value: Any) -> None:
    """Write one file into data/ with the same formatting every time.

    Two-space indent, a trailing newline and an explicit LF line ending
    (matching .gitattributes) are what keeps `git diff` quiet when the same
    value is written twice in a row, including across Windows checkouts
    where the platform default would silently inject CRLF.
    """
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with open(paths.DATA / name, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
