#!/usr/bin/env bash
set -euo pipefail

# Project root (where script is run)
ROOT="$(pwd)"
NAME="$(basename "$ROOT")"
OUT="../${NAME}.tar.gz"

# Ensure we are inside a git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Not inside a git repository"
  exit 1
}

# Create archive excluding .gitignore files
git ls-files --cached --others --exclude-standard -z \
  | tar --null -czf "$OUT" --files-from=-

echo "Archive created: $OUT"