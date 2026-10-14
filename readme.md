# Visual Place Learning in Drosophila melanogaster

An accessible thermal–visual arena and documented analysis workflow for investigating visually guided spatial learning in freely walking flies.

This repository contains research documentation, apparatus development code, and analysis resources. The October 2026 website redesign adds a custom editorial theme, a source-derived LED panorama explorer, calibration tools, current methods, and an explicit distinction between preliminary observations and validated results.

**Intended GitHub Pages address:** https://ajadismail2.github.io/Visual-place-learning/

## Build and review the website

```bash
python -m venv .venv
# Activate this environment using the command appropriate to your shell.
python -m pip install -r requirements-site.txt
python -m mkdocs build --strict
python scripts/verify_site.py
node scripts/verify_interactions.cjs
```

The build writes the static website to `site/`. To view a built copy locally:

```bash
python -m http.server 8000 --directory site
```

Open `http://localhost:8000/`. HTTP is needed for the local search index; directly opening HTML still displays the content but may block search.

## Publishing

The workflow builds and checks pull requests and uploads a downloadable `research-website` artifact. It deploys only pushes or manual runs on `main`, after the checks pass. Enable **Settings → Pages → Build and deployment → Source: GitHub Actions** for the intended address to become available. Pages was reported disabled during the repository audit; a successful local build is not a deployment confirmation.

## Website structure

- `theme/`: custom Jinja templates, homepage, shared navigation, and footer.
- `docs/assets/`: local CSS, JavaScript, conceptual arena diagram, and data figure.
- `docs/research/`: scientific rationale, preliminary observations, and the sociability direction.
- `docs/hardware/`: current apparatus specifications and historical integration notes.
- `docs/methods/`: protocol, metric definitions, and validation.
- `docs/resources/`: provenance, file inventory, references, and development status.
- `docs/downloads/`: protocol metadata, a run-manifest template, and preliminary values.
- `scripts/`: site validation, interaction checks, and reproducible figure generation.

The original hardware and analysis source directories remain intact. Their contents are version-specific: the older closed-loop PID code is not the latest staged open-loop thermal controller, and the earlier analysis scripts do not automatically implement newer GUI conventions. Several original placeholder Python files are empty and are not complete applications.

## Current research specification

The current protocol specifies a 20 cm inner arena, ten flies, ten five-minute trials, and target order **B–C–D–C–B–A–D–C–B–A**. Target success requires at least three seconds inside the target with movement allowed. The recorded 916 px / 20 cm calibration is **45.8 px/cm** and applies only to that recording geometry.

These are implementation and protocol records. The website does not claim independent replication of the original study or completed identity validation of all tracking data. See the documentation for measurement and validation boundaries.

## Updating content

Edit Markdown under `docs/`, then update navigation in `mkdocs.yml` when adding a page. The homepage is in `theme/home.html`; its search-index synopsis is in `docs/index.md`. Keep filenames and relative links consistent. Run the strict build and both verification scripts before publishing.

The displayed preliminary figure is generated from `docs/downloads/preliminary_trial_times.csv` by `scripts/generate_figures.py` (requires Matplotlib). Do not add error bars, fitted trends, or missing trials without their supporting data.

The separately maintained AMADEUS target GUI is documented but not redistributed by this website. It can run its own `--self-test` with its documented dependencies installed. Hardware firmware and mechanical fit require separate validation on the real apparatus.

## Attribution

Foundational assay: Ofstad, Zuker & Reiser (2011), https://doi.org/10.1038/nature10131. Sociability reference: Lobato-Rios, Lam & Ramdya, the selected November 2024 preprint version, https://doi.org/10.1101/2024.11.25.624845.

The parametric butt-hinge reference credits Rohin Gosling in its source header. Original notices are preserved. This update does not assign a new blanket licence to pre-existing code, CAD references, or third-party materials.
