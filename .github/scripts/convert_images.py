#!/usr/bin/env python3
"""
Converts PNG/JPG images to _thumb.webp in place.
Only processes images that don't already have a corresponding _thumb.webp,
or where the source is newer than the existing thumb.
Skips files already named *_thumb.webp to avoid double-converting.
"""

import os
import subprocess
from pathlib import Path

# folders to scan
IMAGE_DIRS = ["pic", "commissions"]
# max width for thumbnails (height scales automatically)
MAX_WIDTH = 1200
QUALITY = 80


def needs_conversion(src: Path, thumb: Path) -> bool:
    if not thumb.exists():
        return True
    return src.stat().st_mtime > thumb.stat().st_mtime


def convert(src: Path, thumb: Path):
    print(f"  converting: {src} → {thumb}")
    result = subprocess.run([
        "convert",          # imagemagick
        str(src),
        "-resize", f"{MAX_WIDTH}x>",   # only downscale, never upscale
        "-quality", str(QUALITY),
        str(thumb)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
    else:
        print(f"  ✅ done")


def main():
    converted = 0
    skipped = 0

    for folder in IMAGE_DIRS:
        if not os.path.isdir(folder):
            continue

        for ext in ("*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG"):
            for src in Path(folder).rglob(ext):
                # skip already-converted thumbnails
                if "_thumb" in src.stem:
                    continue

                thumb = src.with_name(src.stem + "_thumb.webp")

                if needs_conversion(src, thumb):
                    convert(src, thumb)
                    converted += 1
                else:
                    skipped += 1

    print(f"\n✅ Converted: {converted}  Skipped (up to date): {skipped}")


if __name__ == "__main__":
    main()
