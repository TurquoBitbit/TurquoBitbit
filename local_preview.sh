#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# preview.sh — local preview build, mirrors the GitHub Actions workflow
# Usage: bash preview.sh
#
# What it does:
#   1. Copies repo into _preview/ folder (inspect processed files there)
#   2. Runs bundle install if needed
#   3. Runs the same Python preprocessing scripts as the workflow
#   4. Rewrites .md links → .html for local Jekyll serve
#   5. Starts Jekyll serve for local preview
#   6. Cleans up _preview/ on exit (Ctrl+C)
# ─────────────────────────────────────────────────────────────────────────────

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PREVIEW_DIR="$REPO_ROOT/_preview"

# ── Cleanup on exit ───────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "  cleaning up _preview/ ..."
  rm -rf "$PREVIEW_DIR"
  echo "  done."
}
trap cleanup EXIT

# ── Step 1: Copy repo to _preview/ ───────────────────────────────────────────
echo "══════════════════════════════════════════"
echo "  Jekyll Local Preview"
echo "══════════════════════════════════════════"
echo ""
echo "  [1/7] Copying repo to _preview/..."
rm -rf "$PREVIEW_DIR"
cp -r "$REPO_ROOT" "$PREVIEW_DIR"
rm -rf "$PREVIEW_DIR/_preview"
cd "$PREVIEW_DIR"

# ── Step 2: Bundle install if needed ─────────────────────────────────────────
echo "  [2/7] Checking Ruby gems..."
if [ ! -f "$REPO_ROOT/Gemfile" ]; then
  echo "        ⚠️  No Gemfile found in repo root — skipping bundle install."
else
  cp "$REPO_ROOT/Gemfile" .

  if [ ! -f "$REPO_ROOT/Gemfile.lock" ]; then
    # no lockfile at all — first time setup, run full install
    echo "        Gemfile.lock not found — running bundle install..."
    bundle install
    # copy the generated lockfile back to repo root for future runs
    cp Gemfile.lock "$REPO_ROOT/Gemfile.lock"
    echo "        Gemfile.lock saved to repo root."
  else
    cp "$REPO_ROOT/Gemfile.lock" .
    # lockfile exists — check if Gemfile changed since it was last locked
    if [ "$REPO_ROOT/Gemfile" -nt "$REPO_ROOT/Gemfile.lock" ]; then
      echo "        Gemfile is newer than Gemfile.lock — running bundle install..."
      bundle install
      cp Gemfile.lock "$REPO_ROOT/Gemfile.lock"
      echo "        Gemfile.lock updated."
    else
      echo "        gems up to date, skipping bundle install."
    fi
  fi
fi

# ── Step 3: Copy README.md → index.md ────────────────────────────────────────
echo "  [3/7] Renaming README.md → index.md..."
if [ -f README.md ]; then
  cp README.md index.md
  echo "        done."
else
  echo "        README.md not found, skipping."
fi

# ── Step 4: Add Jekyll front matter ──────────────────────────────────────────
echo "  [4/7] Adding front matter..."
python3 .github/scripts/add_front_matter.py

# ── Step 5: Convert images to WebP ───────────────────────────────────────────
echo "  [5/7] Converting images to WebP..."
if ! command -v magick &>/dev/null && ! command -v convert &>/dev/null; then
  echo "        ⚠️  ImageMagick not found — skipping image conversion."
  echo "        Install with: brew install imagemagick"
else
  python3 .github/scripts/convert_images.py
fi

# ── Step 6: Rewrite img tags ─────────────────────────────────────────────────
echo "  [6/7] Rewriting img tags..."
python3 .github/scripts/rewrite_img_tags.py

# ── Step 7: Rewrite .md links → .html ────────────────────────────────────────
echo "  [7/7] Rewriting .md links to .html..."
find . -name "*.md" \
  -not -path "./.github/*" \
  -not -path "./.git/*" \
| while read -r f; do
  sed -i '' 's|\](\(\./[^)]*\)\.md)|\](\1.html)|g' "$f"
  sed -i '' 's|\](\(\./[^)#.]*\))|\](\1.html)|g' "$f"
done
echo "        done."
echo ""
echo "  ✅ Inspect processed files in: _preview/"

# ── Start Jekyll ──────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo "  Starting Jekyll..."
echo "  Open: http://localhost:4000/TurquoBitbit/"
echo "  Press Ctrl+C to stop and clean up _preview/"
echo "══════════════════════════════════════════"
echo ""

if [ -f "$REPO_ROOT/Gemfile" ]; then
  bundle exec jekyll serve --livereload
else
  jekyll serve --livereload
fi