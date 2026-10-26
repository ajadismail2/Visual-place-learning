# Visual place-learning apparatus

Practical documentation for assembling and operating the visual place-learning arena.

The manual is organized into Hardware, Software, Analysis, CAD and Resources. Each section has its own folder, including an `images/` folder for section-specific media.

## Build and check

Requires Python 3.10 or later.

```sh
python -m pip install -r requirements-site.txt
python scripts/package_firmware.py
python -m mkdocs build --strict
python scripts/verify_site.py
python scripts/verify_firmware_docs.py
```

Content is in `docs/`, grouped by documentation section. Shared styling is in `docs/styles/`. The generated output is `site/`.

## Source and measurement

The supplied experiment controller uses a five-minute preheat and accepts 1 to 16 cooling steps. Current settings are recorded in `docs/downloads/protocol.json`; the earlier parameter record is archived separately. Setpoints are not measured temperatures.

## Website

[Website](https://ajadismail2.github.io/Visual-place-learning/)

The workflow checks pull requests and publishes from `main`. In repository Settings → Pages, select **GitHub Actions** as the source to enable publication.
