# Visual place-learning apparatus

Makerspace build documentation for Ajad Ismail's replication of the visual place-learning apparatus described by Ofstad, Zuker & Reiser (2011), doi:10.1038/nature10131.

The website focuses on six connected build topics: arena fabrication, Peltier operation, PCB connections, four independent target channels, visual-angle calculations, and heat transfer across the complete arena. It records how component choices and bench tests shaped the design, using concise articles and build sheets.

## Build locally

Requires Python 3.10 or later and Node.js for the interaction checks.

```sh
python -m pip install -r requirements-site.txt
python -m mkdocs build --strict
python scripts/verify_site.py
node scripts/verify_interactions.cjs
```

Open the generated `site/` through a static HTTP server to use search. Markdown content is in `docs/`, templates in `theme/`, and local CSS/JavaScript in `docs/assets/`.

## What the documentation establishes

The source record combines project conversations, the existing repository, manufacturer documentation, and supplied controller revisions reviewed through 16 October 2026. Current pin assignments and timing defaults are recorded in `docs/downloads/protocol.json`. Source settings are not measured thermal performance.

The current master has a three-minute preheat, ten cooling trials and an all-heating eleventh trial. It requires eleven A–D letters. The 15 October defaults supersede the older PWM sequence and display geometry in the first website draft.

PCB manufacturing details, complete thermal-response curves, final assembly validation, and a cost total are not invented where the records do not establish them. Private CAD and controller/application files are not distributed by this documentation change. Existing hardware and analysis source directories are retained unchanged and may represent earlier revisions.

## GitHub Pages

The workflow validates pull requests and uploads a reviewable static-site artifact. Public deployment runs only from `main`. Enable GitHub Pages with **GitHub Actions** as the source before deployment; then merge the website pull request. A successful build is separate from a successful deployment.
