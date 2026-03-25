#!/bin/sh
# install_hooks.sh — Idempotent hook installer for collaborative file locks
# Copies hook files from .collab/hooks/ to .git/hooks/ and sets permissions.
# Safe to run multiple times — always produces the same result.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_ROOT" ]; then
    echo "Error: Not inside a git repository."
    exit 1
fi

COLLAB_HOOKS="$REPO_ROOT/.collab/hooks"
GIT_HOOKS="$REPO_ROOT/.git/hooks"

if [ ! -d "$COLLAB_HOOKS" ]; then
    echo "Error: .collab/hooks/ directory not found."
    exit 1
fi

INSTALLED=0

for hook in pre-commit post-commit pre-push; do
    SRC="$COLLAB_HOOKS/$hook"
    DST="$GIT_HOOKS/$hook"

    if [ ! -f "$SRC" ]; then
        echo "  Skip: $hook (source not found)"
        continue
    fi

    cp "$SRC" "$DST"
    chmod +x "$DST"
    echo "  ✓ Installed: $hook"
    INSTALLED=$((INSTALLED + 1))
done

echo ""
echo "Done. Installed $INSTALLED hook(s) to .git/hooks/"
echo "Hooks will automatically lock/release files during git operations."
