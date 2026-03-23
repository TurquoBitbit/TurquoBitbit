#!/usr/bin/env python3
"""
Interactive CLI to manage markdown pages across the Jekyll build scripts.
Run this locally when you add a new .md file to your repo.

Updates:
  - .github/scripts/add_front_matter.py  (adds front matter config)
  - .github/scripts/rewrite_img_tags.py  (adds file to MD_FILES list)
  - _config.yml                           (adds file to include: list)

Usage:
  python3 tools/manage_pages.py
"""

import re
import sys
from pathlib import Path

# ── Path config ───────────────────────────────────────────────────────────────
def find_repo_root() -> Path:
    """Find repo root by locating .git folder, works from any subfolder."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise FileNotFoundError("Could not find repo root (.git not found)")

REPO_ROOT       = find_repo_root()
FRONT_MATTER_PY = REPO_ROOT / ".github/scripts/add_front_matter.py"
REWRITE_PY      = REPO_ROOT / ".github/scripts/rewrite_img_tags.py"
CONFIG_YML      = REPO_ROOT / "_config.yml"


# ── Helpers ───────────────────────────────────────────────────────────────────

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")
    print(f"    ✅ updated: {path.relative_to(REPO_ROOT)}")

def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else default

def confirm(prompt: str) -> bool:
    return input(f"{prompt} (y/n): ").strip().lower() == "y"

def list_pages_in_front_matter(content: str) -> list[str]:
    return re.findall(r'"([\w/]+\.md)"\s*:', content)

def list_pages_in_config(content: str) -> list[str]:
    """Extract paths in include: block only — stops at next top-level key."""
    in_include = False
    pages = []
    for line in content.splitlines():
        if re.match(r'^include\s*:', line):
            in_include = True
            continue
        if in_include:
            m = re.match(r'^\s+-\s+(.+)', line)
            if m:
                pages.append(m.group(1).strip())
            elif line.strip() and not line.startswith(' '):
                break   # hit next top-level key (e.g. exclude:), stop
    return pages


# ── Update functions ───────────────────────────────────────────────────────────

def add_to_front_matter(md_path: str, title: str):
    content = read(FRONT_MATTER_PY)
    if md_path in content:
        print(f"    — already in add_front_matter.py, skipping")
        return
    new_entry = f'    "{md_path}": {{\n        "title": "{title}",\n    }},\n'
    content = content.replace(
        "}\n\n\ndef has_front_matter",
        f"{new_entry}}}\n\n\ndef has_front_matter"
    )
    write(FRONT_MATTER_PY, content)


def add_to_rewrite(md_path: str):
    content = read(REWRITE_PY)
    if md_path in content:
        print(f"    — already in rewrite_img_tags.py, skipping")
        return
    new_entry = f'    "{md_path}",\n'
    content = content.replace(
        ']\n\n# matches',
        f'{new_entry}]\n\n# matches'
    )
    write(REWRITE_PY, content)


def add_to_config(md_path: str):
    content = read(CONFIG_YML)
    if md_path in content:
        print(f"    — already in _config.yml, skipping")
        return

    lines = content.splitlines(keepends=True)
    result = []
    in_include = False
    last_include_item = -1   # track index of last - item in include block

    # first pass: find the last item index inside include: block
    for i, line in enumerate(lines):
        if re.match(r'^include\s*:', line):
            in_include = True
            continue
        if in_include:
            if re.match(r'^\s+-\s+', line):
                last_include_item = i
            elif line.strip() and not line.startswith(' '):
                in_include = False  # left the include block

    if last_include_item == -1:
        print(f"    ⚠️  Could not find include: block in _config.yml")
        return

    # second pass: insert new entry right after last include item
    for i, line in enumerate(lines):
        result.append(line)
        if i == last_include_item:
            result.append(f"  - {md_path}\n")

    write(CONFIG_YML, "".join(result))


def remove_from_all(md_path: str):
    for path, pattern in [
        (FRONT_MATTER_PY, rf'    "{re.escape(md_path)}": \{{[^}}]+\}},\n'),
        (REWRITE_PY,      rf'    "{re.escape(md_path)}",\n'),
        (CONFIG_YML,      rf'  - {re.escape(md_path)}\n'),
    ]:
        content = read(path)
        new_content = re.sub(pattern, '', content)
        if new_content != content:
            write(path, new_content)
        else:
            print(f"    — not found in {path.name}, skipping")


def show_all_pages():
    content = read(FRONT_MATTER_PY)
    pages = list_pages_in_front_matter(content)
    print("\n  Pages currently registered:")
    for i, p in enumerate(pages, 1):
        print(f"    {i}. {p}")
    return pages


# ── Main menu ─────────────────────────────────────────────────────────────────

def menu_add():
    print("\n── Add new page ──────────────────────────────────────")
    md_path = ask("  Path to .md file (e.g. commissions/newPage.md or newPage.md)")
    if not md_path.endswith(".md"):
        md_path += ".md"
    # normalize backslashes on Windows
    md_path = md_path.replace("\\", "/")

    default_title = Path(md_path).stem.replace("_", " ").replace("-", " ").title()
    title = ask("  Page title (shown in browser tab)", default=default_title)

    print(f"\n  Adding '{md_path}' with title '{title}' to:")
    add_to_front_matter(md_path, title)
    add_to_rewrite(md_path)
    add_to_config(md_path)
    print("\n  Done! Commit and push to trigger the workflow.")


def menu_remove():
    print("\n── Remove page ───────────────────────────────────────")
    pages = show_all_pages()
    if not pages:
        print("  No pages registered.")
        return

    raw = ask("\n  Enter number(s) to remove (e.g. 1 or 1,3)")
    indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
    to_remove = [pages[i] for i in indices if 0 <= i < len(pages)]
    if not to_remove:
        print("  No valid selection.")
        return

    print(f"\n  Will remove: {', '.join(to_remove)}")
    if confirm("  Confirm?"):
        for md_path in to_remove:
            print(f"\n  Removing {md_path}...")
            remove_from_all(md_path)
        print("\n  Done!")


def menu_list():
    print("\n── Current pages ─────────────────────────────────────")
    show_all_pages()
    config_pages = list_pages_in_config(read(CONFIG_YML))
    print("\n  Pages in _config.yml include:")
    for p in config_pages:
        print(f"    • {p}")


def main():
    print("╔══════════════════════════════════════╗")
    print("║   Jekyll Page Manager                ║")
    print("╚══════════════════════════════════════╝")

    while True:
        print("\n  1. Add new page")
        print("  2. Remove page")
        print("  3. List registered pages")
        print("  4. Exit")

        choice = ask("\n  Choose").strip()

        if choice == "1":
            menu_add()
        elif choice == "2":
            menu_remove()
        elif choice == "3":
            menu_list()
        elif choice == "4":
            print("\n  Bye!\n")
            sys.exit(0)
        else:
            print("  Invalid choice, try again.")


if __name__ == "__main__":
    main()