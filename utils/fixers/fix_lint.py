#!/usr/bin/env python3
"""
Automatic lint fixer for the Database Creator & Management System.
This script will automatically fix common linting issues:
- Remove trailing whitespace
- Fix blank lines with whitespace
- Properly format imports
- Fix unused imports
- Fix long lines

Usage:
python fix_lint.py
"""

import os
import re
import sys
from pathlib import Path

def manually_fix_imports(file_path):
    """Manually fix specific import statements in files."""
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix specific imports in gui.py
    if 'gui.py' in file_path:
        content = re.sub(
            r'from tkinter import (.*), simpledialog',
            r'from tkinter import \1',
            content
        )

    # Fix specific imports in theme_manager.py
    elif 'theme_manager.py' in file_path:
        # Change imports but maintain imports that are actually used
        content = re.sub(
            r'import os\nimport json',
            r'# Required imports for theme manager\nimport os\nimport json',
            content
        )

    # Fix specific imports in test_module.py
    elif 'test_module.py' in file_path:
        content = re.sub(
            r'from database_creator\.templates import get_default_templates',
            r'# Templates are tested elsewhere\n# from database_creator.templates import get_default_templates',
            content
        )

    # Check if we made changes and save if needed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
        return True
    else:
        print(f"No import changes needed in {file_path}")
        return False

def manually_fix_long_lines(file_path):
    """Manually fix specific long lines."""
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for i, line in enumerate(lines):
        line = line.rstrip('\r\n')
        if len(line) > 79:
            # Handle specific long line patterns
            if "=" in line and "(" not in line and ")" not in line:
                # Split at the equals sign
                parts = line.split('=', 1)
                if len(parts) == 2:
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(parts[0].rstrip() + "=\\")
                    new_lines.append(' ' * (indent + 4) + parts[1].lstrip())
                    modified = True
                    continue
            elif "," in line and "(" in line and ")" in line:
                # Split function calls with multiple arguments
                open_idx = line.find('(')
                close_idx = line.rfind(')')
                if open_idx > 0 and close_idx > open_idx:
                    prefix = line[:open_idx + 1]
                    suffix = line[close_idx:]
                    args = line[open_idx + 1:close_idx]

                    # Split args by commas
                    arg_parts = args.split(',')
                    indent = len(line) - len(line.lstrip())

                    # Add first line
                    new_lines.append(prefix)

                    # Add each argument
                    for j, arg in enumerate(arg_parts):
                        arg = arg.strip()
                        if j < len(arg_parts) - 1:
                            new_lines.append(' ' * (indent + 4) + arg + ',')
                        else:
                            new_lines.append(' ' * (indent + 4) + arg)

                    # Add closing part
                    new_lines.append(' ' * indent + suffix)
                    modified = True
                    continue

        # If we didn't modify the line, keep it as-is
        new_lines.append(line)

    # Write the file if modified
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"Fixed long lines in {file_path}")
        return True
    else:
        print(f"No long lines fixed in {file_path}")
        return False

def fix_file(filepath):
    """Fix common linting issues in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count issues before fixing
    whitespace_lines_before = len(re.findall(r'^\s+$', content, re.MULTILINE))
    trailing_whitespace_before = len(re.findall(r'[ \t]+$', content, re.MULTILINE))

    # Fix blank lines with whitespace
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)

    # Fix trailing whitespace
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

    # Count issues after fixing
    whitespace_lines_after = len(re.findall(r'^\s+$', content, re.MULTILINE))
    trailing_whitespace_after = len(re.findall(r'[ \t]+$', content, re.MULTILINE))

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return {
        'whitespace_lines_fixed': whitespace_lines_before - whitespace_lines_after,
        'trailing_whitespace_fixed':
            trailing_whitespace_before - trailing_whitespace_after
    }

def process_directory(directory='.'):
    """Process all Python files in a directory recursively."""
    total_stats = {
        'files_processed': 0,
        'whitespace_lines_fixed': 0,
        'trailing_whitespace_fixed': 0
    }

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                print(f"Processing {filepath}...")

                stats = fix_file(filepath)
                total_stats['files_processed'] += 1
                total_stats['whitespace_lines_fixed'] += stats['whitespace_lines_fixed']
                total_stats['trailing_whitespace_fixed'] += stats['trailing_whitespace_fixed']

    return total_stats

def main():
    """Main function."""
    print("Database Creator & Management System - Advanced Lint Fixer")
    print("=" * 60)

    directory = '.'
    if len(sys.argv) > 1:
        directory = sys.argv[1]

    # Fix basic linting issues first
    stats = process_directory(directory)

    print("\nBasic Fixes Summary:")
    print(f"Files processed: {stats['files_processed']}")
    print(f"Blank lines with whitespace fixed: {stats['whitespace_lines_fixed']}")
    print("Lines with trailing whitespace fixed: "
          f"{stats['trailing_whitespace_fixed']}")

    # Fix specific files with more serious issues
    print("\nFixing specific files with import issues:")
    manually_fix_imports("database_creator/gui.py")
    manually_fix_imports("database_creator/theme_manager.py")
    manually_fix_imports("database_creator/test_module.py")

    print("\nFixing specific files with long line issues:")
    manually_fix_long_lines("database_creator/gui.py")
    manually_fix_long_lines("database_creator/theme_manager.py")
    manually_fix_long_lines("database_creator/test_module.py")

    print("\nLinting fixes complete!")

if __name__ == "__main__":
    main()
