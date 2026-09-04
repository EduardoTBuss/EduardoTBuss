#!/usr/bin/env python3
"""Entry point for the profile toolkit: parse arguments and dispatch.

All behaviour lives in scripts/profile_kit/*; this file stays a thin router
on purpose, so a rule change lives in exactly one module and this file
almost never needs to change. See docs/UPDATING.md for what to edit and why.

    python scripts/generate_visuals.py [--refresh-github] [--render-readme] [--validate-data]

- --refresh-github: fetch public metrics from the GitHub API, write data/github.json.
- --render-readme: regenerate the two stats SVGs from data/github.json, then
  rewrite the three generated blocks of README.md.
- --validate-data: check the JSON data contract; exit 1 on error, print nothing else.
- No flags: validate, then behave like --render-readme, without touching the network.

Data is always validated before anything is written, so a broken
projects.json or publications.json never reaches an SVG or the README.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse  # noqa: E402  (after sys.path fix-up, see above)

from profile_kit import datastore, github_api, readme_blocks, stats_band, validation  # noqa: E402


def _validate_data() -> bool:
    errors = validation.validate()
    if errors:
        print("Data contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return False
    print("Data contract OK.")
    return True


def _render(github_stats: dict) -> None:
    stats_band.write(github_stats)
    readme_blocks.render_readme()
    print("Wrote generated/stats-light.svg, generated/stats-dark.svg and README.md.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--refresh-github", action="store_true",
        help="fetch public GitHub metrics and overwrite data/github.json",
    )
    parser.add_argument(
        "--render-readme", action="store_true",
        help="regenerate the stats SVGs and rewrite the generated blocks of README.md",
    )
    parser.add_argument(
        "--validate-data", action="store_true",
        help="validate the JSON data contract and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    no_flags = not (args.refresh_github or args.render_readme or args.validate_data)
    if no_flags:
        args.validate_data = True
        args.render_readme = True

    if not _validate_data():
        return 1
    if args.validate_data and not (args.refresh_github or args.render_readme):
        return 0

    if args.refresh_github:
        github_api.refresh_github()
        print("Refreshed data/github.json.")

    if args.render_readme:
        _render(datastore.load("github.json"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
