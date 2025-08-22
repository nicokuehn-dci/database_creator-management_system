#!/usr/bin/env python3
"""
Fix syntax errors in the GUI file caused by autopep8.
"""

import os
import re
import sys

def fix_syntax_errors(filepath):
    """Fix syntax errors in the given file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix broken assignments that span lines
    pattern = r'(\s+)([a-zA-Z0-9_.]+)\s*=\s*\n\s+(.+)'
    content = re.sub(pattern, r'\1\2 = \3', content)

    # Fix string literal untermination
    content = content.replace('{os.path.basename(DB_STORAGE_DIR)} folder)",',
                             '{os.path.basename(DB_STORAGE_DIR)} folder)"')

    # Write the content back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed syntax errors in {filepath}")
    else:
        print(f"No syntax errors found in {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_syntax_errors.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} does not exist")
        sys.exit(1)

    fix_syntax_errors(filepath)
