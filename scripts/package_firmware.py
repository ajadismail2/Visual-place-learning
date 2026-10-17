"""Package the reviewed website copies; never reads private uploaded source."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1] / 'docs/downloads'
firmware = root / 'firmware'
manifest_path = root / 'firmware-manifest.json'
manifest = json.loads(manifest_path.read_text())
for item in manifest['files']:
    item['sha256'] = hashlib.sha256((root / item['path']).read_bytes()).hexdigest()
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
archive = root / 'arena-firmware-2026-10-17.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(firmware.rglob('*')):
        if not path.is_file():
            continue
        assert path.name != 'local_config.h', 'Private settings must not be packaged'
        info = zipfile.ZipInfo(path.relative_to(firmware).as_posix(), (2026, 10, 17, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        bundle.writestr(info, path.read_bytes())
paths = [p for p in root.rglob('*') if p.is_file() and p.name != 'SHA256SUMS']
(root / 'SHA256SUMS').write_text(''.join(
    hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(root).as_posix() + '\n'
    for p in sorted(paths)
))
print(f'Packaged {len(manifest["files"])} supplied sketches, configuration example, and syntax-only correction.')
