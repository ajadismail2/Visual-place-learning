# Visual place-learning apparatus

Practical documentation for assembling and operating the visual place-learning arena.

## Build and check

Requires Python 3.10 or later and FFmpeg (including `ffprobe`).

```sh
python -m pip install -r requirements-site.txt
python -m mkdocs build --strict
python scripts/prepare_site_videos.py
python scripts/verify_site.py
python scripts/verify_firmware_docs.py
```

The video step creates H.264 web copies in `site/`; uploaded videos in `docs/` remain unchanged.

[Website](https://ajadismail2.github.io/Visual-place-learning/)

