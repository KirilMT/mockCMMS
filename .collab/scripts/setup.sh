#!/bin/bash
# Collaborative File Locking — Unix Setup
# Run from the project root: bash .collab/scripts/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COLLAB_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$COLLAB_ROOT")"

echo ""
echo "=== Collaborative File Locking — Setup ==="
echo ""

# 1. Check Python
echo "[1/4] Checking Python..."
PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi
if ! command -v "$PYTHON" > /dev/null 2>&1; then
    PYTHON="python"
fi

VERSION=$($PYTHON --version 2>&1)
echo "  ✓ $VERSION"

# 2. Check supabase package
echo "[2/4] Checking supabase package..."
if $PYTHON -c "import supabase" 2>/dev/null; then
    echo "  ✓ supabase-py is installed"
else
    echo "  Installing supabase-py..."
    $PYTHON -m pip install supabase python-dotenv --quiet
    echo "  ✓ supabase-py installed"
fi

# 3. Check .env
echo "[3/4] Checking .env file..."
ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    if grep -q "SUPABASE_URL=" "$ENV_FILE" && grep -q "SUPABASE_ANON_KEY=" "$ENV_FILE"; then
        echo "  ✓ .env has Supabase credentials"
    else
        echo "  ⚠ .env exists but may be missing Supabase credentials."
        echo "  Reference: .collab/.env.example"
    fi
else
    echo "  ⚠ .env not found. Copy .collab/.env.example to .env"
fi

# 4. Install hooks
echo "[4/4] Installing git hooks..."
bash "$COLLAB_ROOT/hooks/install_hooks.sh"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Ensure .env has SUPABASE_URL and SUPABASE_ANON_KEY set"
echo "  2. Run the schema in Supabase SQL Editor: .collab/schema.sql"
echo "  3. Test: python collab.py active"
echo ""
