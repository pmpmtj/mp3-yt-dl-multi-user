#!/usr/bin/env python3
# my_project/path_utils/demo_path_utils.py
"""
Demo script showing usage of path_utils functions
"""

from path_utils import get_script_directories, resolve_path
from pathlib import Path
import sys
import os

# Add parent directory to path to import from src.common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.common.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger("demo_path_utils")

def main():
    logger.info("Starting Path Utils Demo")
    print("=== Path Utils Demo ===\n")
    
    # Demo get_script_directories()
    logger.debug("Testing get_script_directories()")
    print("1. get_script_directories():")
    script_dir, base_dir = get_script_directories()
    print(f"   SCRIPT_DIR: {script_dir}")
    print(f"   BASE_DIR: {base_dir}")
    logger.debug(f"Retrieved directories - SCRIPT_DIR: {script_dir}, BASE_DIR: {base_dir}")
    print()
    
    # Demo resolve_path() with different inputs
    logger.debug("Testing resolve_path() with various inputs")
    print("2. resolve_path() examples:")
    
    # Relative path (resolves against BASE_DIR)
    relative_path = resolve_path("src/common")
    print(f"   resolve_path('src/common'): {relative_path}")
    logger.debug(f"Resolved relative path 'src/common' to: {relative_path}")
    
    # Absolute path (returns as-is)
    abs_path = resolve_path("/absolute/path/to/file")
    print(f"   resolve_path('/absolute/path/to/file'): {abs_path}")
    logger.debug(f"Resolved absolute path to: {abs_path}")
    
    # Relative path with custom base
    custom_base = Path("C:/custom/base")
    custom_path = resolve_path("subfolder/file.txt", custom_base)
    print(f"   resolve_path('subfolder/file.txt', custom_base): {custom_path}")
    logger.debug(f"Resolved custom path to: {custom_path}")
    
    logger.info("Path Utils Demo completed successfully")
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
