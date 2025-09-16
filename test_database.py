#!/usr/bin/env python3
"""
test_database.py

Main database test script for the project.
Runs comprehensive database tests using the organized database package.

This script follows the project's architecture guidelines:
- Uses centralized logging from /src/common/logging_config.py
- Uses path utilities from /path_utils/path_utils.py
- Handles both frozen (PyInstaller) and regular Python execution
- Self-contained module with proper error handling
- Production-minded development approach
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from src.database.tests.run_all_tests import main

if __name__ == "__main__":
    sys.exit(main())
