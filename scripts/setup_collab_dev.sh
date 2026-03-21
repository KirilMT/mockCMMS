#!/bin/bash
# setup_collab_dev.sh
#
# Install collaborative development hooks and verify lock server connectivity.
# Run this once after cloning or pulling the new hooks.
#
# Usage:
#   bash scripts/setup_collab_dev.sh

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_SOURCE="$REPO_ROOT/.github/hooks"
HOOKS_DEST="$REPO_ROOT/.git/hooks"

echo "🔧 Setting up collaborative development environment..."

# Install hooks
for hook in pre-commit pre-push; do
  if [ -f "$HOOKS_SOURCE/$hook" ]; then
    cp "$HOOKS_SOURCE/$hook" "$HOOKS_DEST/$hook"
    chmod +x "$HOOKS_DEST/$hook"
    echo "✅ Installed hook: $hook"
  fi
done

# Check lock server
LOCK_SERVER_URL="${LOCK_SERVER_URL:-http://localhost:5001}"
if curl -sf "${LOCK_SERVER_URL}/api/locks/health" > /dev/null 2>&1; then
  echo "✅ Lock server reachable at $LOCK_SERVER_URL"
else
  echo "⚠️  Lock server not reachable at $LOCK_SERVER_URL"
  echo "   Start it with: python -m src.services.lock_manager_app"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start lock server:   python -m src.services.lock_manager_app"
echo "  2. View dashboard:      http://localhost:5001/admin/lock-dashboard"
echo "  3. Check a file:        python -m src.services.lock_client status src/services/db_utils.py"
