#!/usr/bin/env python3
"""
Rewrites <img src="./path/image.png"> in markdown files to:
  <a href="./path/image.png"><img src="./path/image_thumb.webp"></a>

Only runs on jekyll_branch (not master).
Only rewrites tags where a corresponding _thumb.webp actually exists.
Safe to run multiple times — won't double-wrap already-wrapped images.
"""

import re
from pathlib import Path

# markdown files to process
MD_FILES = [
    "index.md",
    "README_EN.md",
    "commissions/cardBadge.md",
    "commissions/pulexStickerBase.md",
]

# matches <img src="./some/path.png" ...> or <img src="./some/path.jpg" ...>
# captures: prefix attrs before src, the src path, and any remaining attrs
IMG_TAG = re.compile(
    r'<img\s([^>]*?)src="(\./[^"]+\.(png|jpg|jpeg))"([^>]*)>',
    re.IGNORECASE
)

# detect already-wrapped images to avoid double-wrapping
ALREADY_WRAPPED = re.compile(
    r'<a\s[^>]*href="[^"]+"><img\s[^>]*src="[^"]*_thumb\.webp"[^>]*></a>',
    re.IGNORECASE
)


def thumb_path(src: str) -> str:
    """Given ./pic/foo.png returns ./pic/foo_thumb.webp"""
    p = Path(src)
    return str(p.with_name(p.stem + "_thumb.webp"))


def thumb_exists(src: str) -> bool:
    # src is like ./pic/foo.png — strip leading ./
    local = src.lstrip("./")
    thumb = Path(local).with_name(Path(local).stem + "_thumb.webp")
    return thumb.exists()


def rewrite(content: str) -> tuple[str, int]:
    count = 0

    def replace(m):
        nonlocal count
        pre_attrs = m.group(1)
        src = m.group(2)
        post_attrs = m.group(4)

        # skip if no thumbnail exists for this image
        if not thumb_exists(src):
            print(f"  skipping (no thumb): {src}")
            return m.group(0)

        thumb = thumb_path(src)
        count += 1
        return f'<a href="{src}"><img {pre_attrs}src="{thumb}"{post_attrs}></a>'

    # skip lines that are already wrapped
    lines = content.split("\n")
    result = []
    for line in lines:
        if ALREADY_WRAPPED.search(line):
            result.append(line)   # already done, leave it
        else:
            result.append(IMG_TAG.sub(replace, line))

    return "\n".join(result), count


def main():
    for md_path in MD_FILES:
        p = Path(md_path)
        if not p.exists():
            print(f"skipping (not found): {md_path}")
            continue

        original = p.read_text(encoding="utf-8")
        rewritten, count = rewrite(original)

        if count > 0:
            p.write_text(rewritten, encoding="utf-8")
            print(f"✅ {md_path}: {count} image(s) rewritten")
        else:
            print(f"— {md_path}: nothing to rewrite")


if __name__ == "__main__":
    main()
