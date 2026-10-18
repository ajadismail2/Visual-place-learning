# Visual place-learning apparatus

Makerspace build documentation for Ajad Ismail's replication of the apparatus described by Ofstad, Zuker & Reiser, doi:10.1038/nature10131.

The site covers arena fabrication, Peltier control, PCB and ESP32 wiring, four cooling tiles, visual angles, and heat removal. Eight supplied sketches are explained and available in full.

## Build and check

Requires Python 3.10 or later and Node.js.

```sh
python -m pip install -r requirements-site.txt
python scripts/package_firmware.py
python -m mkdocs build --strict
python scripts/verify_site.py
python scripts/verify_firmware_docs.py
node scripts/verify_interactions.cjs
```

Content is in `docs/`, templates in `theme/`, and local CSS/JavaScript in `docs/assets/`. The output is `site/`.

## Source and measurement

The supplied master uses a five-minute preheat and accepts 1 to 16 cooling steps. Current settings are recorded in `docs/downloads/protocol.json`; the earlier parameter record is archived separately. Setpoints are not measured temperatures.

Measured temperature logs and STEP files are awaiting upload. The CNC-cut carrier, lower heat sinks, and thermal-controller ESP32 conversion are labelled proposals, not completed or validated hardware.

Personal AP credentials and the device MAC are excluded from published code. Configure the master locally using `local_config.example.h`. The original ring sketch's syntax error is documented, with a separate syntax-only correction. No firmware compilation or hardware test is claimed.

## Website

[Website](https://ajadismail2.github.io/Visual-place-learning/) · [Download QR code](docs/downloads/website-qr.png)

The workflow checks pull requests and publishes from `main`. In repository Settings → Pages, select **GitHub Actions** as the source to enable publication.

## Editable QR destination

[Download print PNG](docs/downloads/website-dynamic-qr.png) · [Download vector SVG](docs/downloads/website-dynamic-qr.svg)

The QR encodes the permanent address `https://ajadismail2.github.io/Visual-place-learning/go/`. GitHub Pages must be enabled before scans work. Preparing these files does not enable Pages.

To change where existing printed codes lead, edit the `url` in `docs/go/target.json`, commit the change, and let the Pages workflow publish it. Use an HTTPS destination. Keep the repository name, Pages domain and `/go/` path unchanged. Allow the deployment and hosting caches to update before checking the new destination.

The default destination is the future GitHub Pages homepage. There is no tracking service or third-party QR subscription. The image itself is fixed; the hosted redirect makes its destination editable. If JavaScript or the configuration request fails, the page provides a homepage link. Update that fallback in `docs/go/index.html` too if the homepage moves.
