#!/usr/bin/env python3
"""
Adds Jekyll front matter to markdown files if not already present.
Safe to run multiple times — detects existing front matter and skips.
"""

from pathlib import Path

# Define front matter per file
# Add new pages here as your site grows
FRONT_MATTER = {
    "index.md": {
        "title": "韜光",
    },
    "README_EN.md": {
        "title": "Turquo the Cabbit",
    },
    "commissions/cardBadge.md": {
        "title": "cardBadge",
    },
    "commissions/pulexStickerBase.md": {
        "title": "pulexStickerBase",
    },
}


def has_front_matter(content: str) -> bool:
    """Returns True if file already starts with a --- front matter block."""
    return content.lstrip().startswith("---")


def build_front_matter(fields: dict) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f'{key}: "{value}"')
    lines.append("---")
    lines.append("")   # blank line after front matter
    return "\n".join(lines)


def main():
    for md_path, fields in FRONT_MATTER.items():
        p = Path(md_path)
        if not p.exists():
            print(f"  skipping (not found): {md_path}")
            continue

        content = p.read_text(encoding="utf-8")

        if has_front_matter(content):
            print(f"  — {md_path}: front matter already present, skipping")
            continue

        front = build_front_matter(fields)
        p.write_text(front + content, encoding="utf-8")
        print(f"  ✅ {md_path}: front matter added")


if __name__ == "__main__":
    main()
