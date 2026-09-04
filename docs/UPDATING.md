# Updating this profile

There are now two repositories. This one (`EduardoTBuss`) owns the data and the README;
`EduardoTBuss.github.io` owns the site and only reads what lives here. Keep that direction
one-way: never hand-edit a JSON file from the site repo.

## The rule of thumb

> What changes weekly lives on the site. This README only carries what is stable for
> months. If you felt the urge to update the README twice in the same month, the content
> was in the wrong place.

Numbers that move often (repo count, followers, stars) are generated from `data/github.json`
every day by the workflow. Prose that moves often (a new project write-up, an in-progress
paper's full abstract) belongs on `eduardotbuss.github.io`, not here.

## I want to change X -> edit Y

| I want to... | Edit | Then |
|---|---|---|
| Fix my bio, links, name | `data/profile.json` | site picks it up on its next build; README bio is hand-written in `README.md`, update both |
| Add/reorder/retire a pinned project | `data/projects.json` | run `--validate-data`; `--render-readme` updates the README table; the site regenerates its project list and pages |
| Add a publication | `data/publications.json`, with a new stable `id` | run `--validate-data`; `--render-readme` updates the "Recent publications" list if it is one of the 3 most recent |
| Link a publication to a project | `projects[].publications` in `data/projects.json`, using the publication's `id` | run `--validate-data` -- it fails loudly if the `id` does not exist |
| Update current research directions | `data/research.json` (site) and the "About" prose in `README.md` (hand-written, do it yourself) | -- |
| Update "what I'm doing now" | `data/now.json` (site's Now section) and the "Currently" bullets in `README.md` if they changed for months, not weeks | -- |
| Update the CV | `data/cv.json` | site CV section picks it up; no README block depends on it |
| Change the projects table's columns or the publication citation format | `scripts/profile_kit/readme_blocks.py` | one file, one function per block |
| Change the stats strip's palette, layout or fields | `scripts/profile_kit/stats_band.py` | constants are at the top of the file |
| Change how GitHub is queried, or what gets computed from the API response | `scripts/profile_kit/github_api.py` | -- |
| Change the validation rules | `scripts/profile_kit/validation.py` | -- |
| Change where files live on disk | `scripts/profile_kit/paths.py` | -- |
| Change what runs, or add a CLI flag | `scripts/generate_visuals.py` | stays a thin dispatcher on purpose, see its module docstring |

## The generator: `scripts/generate_visuals.py`

Stdlib-only Python (no `requirements.txt`, no CI cache to manage). The logic lives in
`scripts/profile_kit/`, one module per responsibility:

- `paths.py` -- where files live; every other module asks this one.
- `datastore.py` -- read/write `data/*.json`.
- `validation.py` -- the data contract checks (schema, cross-references).
- `github_api.py` -- talks to the GitHub REST API, writes `data/github.json`.
- `stats_band.py` -- draws the two stats SVGs.
- `readme_blocks.py` -- renders the three generated blocks of `README.md`.

```bash
python scripts/generate_visuals.py --validate-data     # check the data contract, exit 1 on error
python scripts/generate_visuals.py --refresh-github    # fetch public GitHub metrics
python scripts/generate_visuals.py --render-readme     # regenerate the stats SVGs + rewrite README blocks
python scripts/generate_visuals.py                     # validate + render-readme, no network
```

`--refresh-github` works without a `GITHUB_TOKEN` locally (prints a warning and calls the
API unauthenticated, 60 requests/hour). In CI, the workflow passes `GITHUB_TOKEN` for free
(no new secret) so the daily cron gets 5000 requests/hour instead of racing every other
unauthenticated caller on the runner's shared IP.

## Marked blocks in `README.md`

Three pairs of HTML comments mark generated content; everything outside them is prose you
write by hand and `--render-readme` never touches:

- `<!-- projects:start -->` / `<!-- projects:end -->` -- the pinned projects table.
- `<!-- publications:start -->` / `<!-- publications:end -->` -- the 3 most recent publications.
- `<!-- stats:start -->` / `<!-- stats:end -->` -- the `<picture>` stats strip.

If a marker is missing or out of order, `--render-readme` raises an error and writes
nothing, rather than corrupting the file.

## The stats strip

`generated/stats-light.svg` and `generated/stats-dark.svg` are drawn from `data/github.json`
by `stats_band.py`. No `github-readme-stats`-style third-party service: it rate-limits and
occasionally serves a broken card. Both files render identically today: the real defense
against GitHub's light/dark split is a transparent background and a single neutral color
(`#7d8590`) legible on both themes, because `prefers-color-scheme` inside an `<img>` tracks
the visitor's OS, not the theme picked on github.com. `<picture>` is still wired up so a
future tone refinement is a change inside `stats_band.py` alone.

## Automation

`.github/workflows/update-profile.yml` runs daily (`17 9 * * *` UTC) and on `workflow_dispatch`,
plus on push to `main` when a content or generator file changes. It validates, refreshes
`data/github.json`, re-renders `README.md`, and commits `data/github.json`, `generated/` and
`README.md` as `github-actions[bot]` if anything changed. `README.md` is excluded from the
push trigger's path list so the bot's own commit can never start another run.

## What is preserved but retired

The old animated dashboard (`generated/profile.svg` and friends, and the ~900 extra lines of
Python that drew it) still exists in full on the `legacy/svg-dashboard` branch, untouched.
Nothing was deleted from history, only from `main`.
