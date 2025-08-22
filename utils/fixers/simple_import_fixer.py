#!/usr/bin/env python3
"""
Simple Import Fixer for Database Creator project.
This script removes only unused imports from specific files.
"""

import sys
import re

def fix_imports(file_path):
    """
    Fix imports in a single file
    """
    print(f"Processing {file_path}...")

    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Store original content for comparison
    original_content = content

    # Remove unused imports
    if 'gui.py' in file_path:
        # Remove simpledialog from tkinter imports
        content = re.sub(r'from tkinter import (.*), simpledialog(.*)',
                         r'from tkinter import \1\2', content)

        # Remove typing imports
        content = re.sub(r'from typing import .*', '', content)

        # Remove security import
        content = re.sub(r'from \.security import hash_password\n', '', content)

    # Check if we made changes
    if content != original_content:
        # Write the changes back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
    else:
        print(f"No changes needed in {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_fixer.py <file_path>")
        sys.exit(1)

    fix_imports(sys.argv[1])
