import sys
import os

# Add the monorepo root to sys.path
# This allows imports like 'from packages.mockCMMS.src.app import create_app' to work
current_dir = os.path.dirname(os.path.abspath(__file__))
monorepo_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, monorepo_root)

from packages.mockCMMS.src.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Use a different port than workforceManager (5000)