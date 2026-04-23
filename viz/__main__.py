#!/usr/bin/env python3
"""
Entry point for running viz as a module: python -m viz
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from viz.main import main

if __name__ == "__main__":
    main()
