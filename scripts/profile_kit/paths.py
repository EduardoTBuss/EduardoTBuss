"""Single owner of the repository layout.

Every other module asks this one where files live, so moving a directory is a
one-file change.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
README = ROOT / "README.md"


def write_text_artifact(path: Path, content: str) -> Path:
    """Write generated text with trailing whitespace stripped and LF endings.

    Normalising here is what makes re-running the generator produce no diff on
    Windows checkouts, where the default newline translation would be CRLF.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(normalized)
    return path


def write_generated(name: str, content: str) -> Path:
    """Write an artifact into generated/."""
    return write_text_artifact(GENERATED / name, content)
