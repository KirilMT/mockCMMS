import sys
import os

# Add the project root to the Python path
# This allows tests to import modules from 'src' as if they were top-level packages
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

