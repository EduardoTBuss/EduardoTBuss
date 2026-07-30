# Updating this profile

The visual profile is generated from small JSON files. You do not need to edit the SVG by hand.

## Change the content

- `data/profile.json`: identity, bio, interests and links.
- `data/research.json`: current research directions.
- `data/projects.json`: selected repositories and their research-to-code connection.
- `data/publications.json`: publications, venue, status and links.
- `data/github.json`: public GitHub metrics, updated automatically when requested.

When one of the editable content JSON files is changed on `main`, GitHub Actions regenerates and commits the SVGs automatically. The scheduled workflow also refreshes public GitHub metrics once per day. Generated SVG files should not be edited by hand.

Publication status should be explicit: `published`, `accepted`, `submitted`, or `in preparation`.
Do not add a DOI or paper URL until it is verified.

## Regenerate the visuals

```bash
python scripts/generate_visuals.py
```

To refresh public profile/repository metrics from GitHub first:

```bash
python scripts/generate_visuals.py --refresh-github
```

Generated files are written to `generated/` and are committed because GitHub renders them from the repository. `generated/profile.svg` is the single self-contained dashboard used by the README. It uses a horizontal composition, fills the available README width, follows the viewer's light or dark color scheme and hides secondary detail on narrow viewports. Four small `nav-*.svg` files are wrapped in regular README links so the navigation remains genuinely clickable on GitHub. The separate module SVGs remain available for focused editing and testing, but are not displayed by the README.

The background dust is generated deterministically inside `dashboard_profile()`. It uses CSS-only motion, does not require JavaScript and becomes static when the viewer prefers reduced motion. Its three global controls are near the top of `scripts/generate_visuals.py`:

- `tamanho_particula`: base grain size.
- `cor_particula`: shared CSS/hex color.
- `aleatoriedade_particula`: amount of variation in count, position, shape, speed and trajectory, from `0.0` to `1.0`.

The dashboard follows an explicit visual stack: background and grid, translucent panel surfaces, ambient particles, then meaningful text and diagrams. This lets grains pass over each module surface without obscuring its content.

The dashboard starts as an almost empty field and coordinates its grid, signal buses, panel outlines and content over approximately six seconds. Keep the timing centralized in `dashboard_profile()` so later changes remain synchronized. Reduced-motion preferences skip directly to the completed state.

The displayed circuit is the only VQC in the dashboard. It is a generic, theoretically coherent illustrative model: angle encoding, parameterized `RY/RZ` layers, a three-gate nearest-neighbor `CX` chain connecting all four qubits, `Z` expectation values and a classical parameter-update loop. Replace its topology when a specific paper or experiment should be represented.

The neural panel contains stationary layer nodes only. Its animation activates connections and layers in sequence; no particle travels along an edge.

## Preview

Open the generated SVG files in a browser, then preview `README.md` on GitHub. The SVGs include a reduced-motion fallback and remain readable after animation ends.
