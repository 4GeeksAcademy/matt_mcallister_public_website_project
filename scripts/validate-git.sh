#!/usr/bin/env bash
set -euo pipefail

git diff --check
git fsck --no-reflogs --full >/dev/null

if [[ -n "$(git ls-files -u)" ]]; then
  echo "Unresolved Git index conflicts found." >&2
  exit 1
fi

if git grep -n -E '^(<<<<<<<|>>>>>>>)' -- .; then
  echo "Textual merge conflict markers found." >&2
  exit 1
fi

forbidden="$(
  git ls-files |
    rg '(^|/)(node_modules|\.next|__pycache__)(/|$)|(^|/)\.env$|\.pyc$|\.coverage$|\.sqlite3?$|(^|/)dist/' ||
    true
)"

if [[ -n "$forbidden" ]]; then
  echo "Tracked generated, local, or sensitive files found:" >&2
  echo "$forbidden" >&2
  exit 1
fi
