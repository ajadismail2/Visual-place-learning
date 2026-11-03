"""Create browser-compatible MP4 copies in the generated site directory."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "site"


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def prepare(source):
    destination = SITE / source.relative_to(DOCS).with_suffix(".web.mp4")
    if not destination.parent.is_dir():
        raise RuntimeError("Build the site with MkDocs before preparing videos.")
    original = probe(source)
    original_video = next(s for s in original["streams"] if s["codec_type"] == "video")
    print(f"Preparing {source.relative_to(ROOT)}", flush=True)
    with tempfile.TemporaryDirectory(prefix="site-video-") as temporary:
        output = Path(temporary) / "video.mp4"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?",
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-threads", "2", "-pix_fmt", "yuv420p", "-tag:v", "avc1",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                str(output),
            ],
            check=True,
        )
        converted = probe(output)
        video = next(s for s in converted["streams"] if s["codec_type"] == "video")
        if video["codec_name"] != "h264" or video["pix_fmt"] != "yuv420p":
            raise RuntimeError(f"Browser video encoding failed: {source}")
        if "mp4" not in converted["format"]["format_name"].split(","):
            raise RuntimeError(f"Expected an MP4 container: {source}")
        for dimension in ("width", "height"):
            expected = (original_video[dimension] + 1) // 2 * 2
            if video[dimension] != expected:
                raise RuntimeError(f"Video dimensions changed unexpectedly: {source}")
        if abs(float(original["format"]["duration"]) - float(converted["format"]["duration"])) > 0.5:
            raise RuntimeError(f"Video duration changed unexpectedly: {source}")
        shutil.copyfile(output, destination)
    print(f"Created {destination.relative_to(ROOT)} ({destination.stat().st_size / 1024**2:.1f} MiB)", flush=True)


def main():
    for executable in ("ffmpeg", "ffprobe"):
        if shutil.which(executable) is None:
            raise SystemExit(f"Install FFmpeg (including {executable}) before preparing site videos.")
    videos = sorted(p for p in DOCS.rglob("*") if p.is_file() and p.suffix.lower() == ".mp4")
    for source in videos:
        prepare(source)
    print(f"PASS: prepared {len(videos)} browser-compatible videos.")


if __name__ == "__main__":
    main()
