"""
conftest.py
-----------
Pytest configuration. Adds the project root to sys.path so imports work
without needing to install the package.
"""

import os
import sys

# ensure the project root is always on the path when tests run
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
