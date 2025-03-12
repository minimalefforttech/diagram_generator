#!/usr/bin/env python3
"""Runner script for diagram generator."""

import os
import sys
from pathlib import Path

# Add python path if not set
project_root = Path(__file__).parent
python_path = str(project_root / 'python')
if python_path not in sys.path:
    sys.path.insert(0, python_path)
    os.environ['PYTHONPATH'] = python_path

# Now we can import from our package
from diagram_generator.cli import main

if __name__ == "__main__":
    sys.exit(main())
