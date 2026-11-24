#!/usr/bin/env bash
# Build every TikZ block diagram in figures/diagrams/tikz into an SVG next to
# this script.  Requires XeLaTeX (TeX Live with TikZ), the Inter font and
# pdftocairo (poppler-utils).  Usage: figures/diagrams/build.sh [name ...]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
src="$here/tikz"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
names=("$@")
if [ ${#names[@]} -eq 0 ]; then
  for f in "$src"/*.tex; do
    # Only standalone documents are diagrams; style.tex and macro files are inputs.
    if grep -q '\\documentclass' "$f"; then names+=("$(basename "$f" .tex)"); fi
  done
fi
for b in "${names[@]}"; do
  cp "$src/$b.tex" "$tmp/"
  ( cd "$tmp" && TEXINPUTS="$src//:" xelatex -interaction=nonstopmode -halt-on-error "$b.tex" > "$b.out" 2>&1 ) || {
    echo "xelatex failed for $b"; tail -40 "$tmp/$b.out"; exit 1; }
  if grep -q "Missing character" "$tmp/$b.log"; then
    echo "warning: missing glyphs in $b"; grep "Missing character" "$tmp/$b.log" | sort -u
  fi
  pdftocairo -svg "$tmp/$b.pdf" "$here/$b.svg"
  echo "built figures/diagrams/$b.svg"
done
