#!/usr/bin/env bash
# Regenerate the dataset and publish it as a GitHub release; run from a clean main.
set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(git branch --show-current)" != main ]] || ! git diff --quiet HEAD; then
  echo "release.sh needs a clean main checkout" >&2
  exit 1
fi
git pull --ff-only

version="v$(date +%Y.%-m.%-d)"
if gh release view "$version" >/dev/null 2>&1; then
  echo "Release $version already exists" >&2
  exit 1
fi

uv run --no-project --with-requirements requirements.txt make clean tools.csv

if git diff --quiet -- packages.csv tools.csv; then
  echo "No changes to the dataset, nothing to release"
  exit 0
fi
git diff --stat -- packages.csv tools.csv

git commit -m "[data] Update dataset to $version" -- packages.csv tools.csv
git push origin main
gh release create "$version" --target "$(git rev-parse HEAD)" --title "$version" \
  --notes "Dataset update for $(date +%B\ %Y)." packages.csv tools.csv
