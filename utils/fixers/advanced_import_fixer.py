#!/usr/bin/env python3
"""
Advanced Import Fixer for Database Creator project.
This script fixes unused imports and long lines in Python files.
"""

import os
import re
import sys
import argparse
from pathlib import Path

def remove_unused_imports(file_path):
    """
    Removes unused imports from a Python file using regular expressions.

    Args:
        file_path: Path to the Python file to process

    Returns:
        tuple: (modified_content, removed_count)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Known unused imports from flake8 output
    unused_imports = [
        r'tkinter\.simpledialog',
        r'typing\.Dict',
        r'typing\.Any',
        r'typing\.List',
        r'typing\.Callable',
        r'typing\.Optional',
        r'\.security\.hash_password'
    ]

    removed_count = 0

    # First try to remove specific imports from import statements
    for imp in unused_imports:
        # Pattern for "from x import y, z" style imports
        pattern = rf'from [^\n]+ import [^\n]*({imp})[^\n]*'
        matches = re.findall(pattern, content)

        if matches:
            # If we found matches, now we need to carefully remove just that import
            lines = content.split('\n')
            new_lines = []

            for line in lines:
                if re.search(rf'import .*{imp}', line):
                    # For imports in the middle of a comma-separated list
                    if ',' in line:
                        parts = line.split(',')
                        filtered_parts = [p for p in parts if not re.search(imp, p)]
                        if filtered_parts:
                            new_line = ','.join(filtered_parts)
                            new_lines.append(new_line)
                        else:
                            # Skip this line entirely if all imports are removed
                            removed_count += 1
                    else:
                        # Skip this line as it's just a single import
                        removed_count += 1
                else:
                    new_lines.append(line)

            content = '\n'.join(new_lines)

    # Now look for entire unused import lines
    for imp in unused_imports:
        pattern = rf'^import {imp}$|^from [^\n]+ import {imp}$'
        matches = re.findall(pattern, content, re.MULTILINE)
        removed_count += len(matches)
        content = re.sub(pattern, '', content, flags=re.MULTILINE)

    # Remove multiple consecutive blank lines resulting from import removal
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Check if we made changes
    if content != original_content:
        return content, removed_count

    return None, 0

def fix_long_lines(file_path, max_length=79):
    """
    Fix long lines by breaking them at appropriate places.

    Args:
        file_path: Path to the Python file to process
        max_length: Maximum allowed line length

    Returns:
        tuple: (modified_content, fixed_count)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_content = []
    fixed_count = 0

    for line in lines:
        line = line.rstrip('\r\n')
        if len(line) > max_length:
            # Don't break lines that are comments or docstrings
            if line.lstrip().startswith('#') or '"""' in line or "'''" in line:
                modified_content.append(line)
                continue

            # Try to break before function calls and parameters
            if re.search(r'\(.*,', line) and '(' in line and ')' in line:
                # Break long function calls by splitting at commas
                indent = len(line) - len(line.lstrip())
                additional_indent = 4  # additional indent for parameters

                # Split at the opening parenthesis and indent parameters
                opening_paren_pos = line.find('(')
                if opening_paren_pos > 0 and opening_paren_pos < max_length - 10:
                    before_paren = line[:opening_paren_pos + 1]
                    after_paren = line[opening_paren_pos + 1:]

                    if after_paren.strip():
                        # Split parameters by commas
                        params = after_paren.split(',')
                        param_lines = []
                        param_lines.append(before_paren)

                        for i, param in enumerate(params):
                            if i < len(params) - 1:  # All but the last param
                                param_line = ' ' * (indent + additional_indent) + param.strip() + ','
                            else:  # Last param
                                param_line = ' ' * (indent + additional_indent) + param.strip()
                            param_lines.append(param_line)

                        modified_content.extend(param_lines)
                        fixed_count += 1
                        continue

            # Try to break string concatenations
            if '+' in line and ('"' in line or "'" in line):
                indent = len(line) - len(line.lstrip())
                additional_indent = 4

                parts = line.split('+')
                if len(parts) > 1:
                    modified_content.append(parts[0].rstrip() + '+')
                    for part in parts[1:-1]:
                        modified_content.append(' ' * (indent + additional_indent) + part.strip() + '+')
                    modified_content.append(' ' * (indent + additional_indent) + parts[-1].strip())
                    fixed_count += 1
                    continue

            # Break long assignments
            if '=' in line and not '==' in line:
                indent = len(line) - len(line.lstrip())
                parts = line.split('=', 1)
                if len(parts[0]) < max_length - 10:
                    modified_content.append(parts[0] + '=')
                    modified_content.append(' ' * (indent + 4) + parts[1].strip())
                    fixed_count += 1
                    continue

        # If we didn't modify the line, keep it as-is
        modified_content.append(line)

    return '\n'.join(modified_content) + '\n', fixed_count

def process_file(file_path, fix_imports=True, fix_lines=True, max_length=79, dry_run=False):
    """
    Process a single Python file to fix imports and long lines.

    Args:
        file_path: Path to the Python file to process
        fix_imports: Whether to fix unused imports
        fix_lines: Whether to fix long lines
        max_length: Maximum allowed line length
        dry_run: If True, don't modify files, just report

    Returns:
        dict: Statistics about changes made
    """
    stats = {'imports_removed': 0, 'lines_fixed': 0}
    file_path = Path(file_path)

    if not file_path.exists() or not file_path.is_file():
        print(f"Warning: {file_path} does not exist or is not a file")
        return stats

    modified = False
    content = None

    # First fix imports if requested
    if fix_imports:
        content, removed_count = remove_unused_imports(file_path)
        if content is not None and removed_count > 0:
            stats['imports_removed'] = removed_count
            modified = True

    # Then fix long lines if requested
    if fix_lines:
        if content is None:
            # If we haven't modified the content yet, read from file
            file_content, fixed_count = fix_long_lines(file_path, max_length)
        else:
            # Use the already modified content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            file_content, fixed_count = fix_long_lines(file_path, max_length)

        if fixed_count > 0:
            content = file_content
            stats['lines_fixed'] = fixed_count
            modified = True

    # Write back changes if modified and not in dry run mode
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Modified {file_path}: removed {stats['imports_removed']} imports, fixed {stats['lines_fixed']} long lines")
    elif modified:
        print(f"Would modify {file_path}: removed {stats['imports_removed']} imports, fixed {stats['lines_fixed']} long lines")

    return stats

def process_directory(directory, extension='.py', fix_imports=True, fix_lines=True, max_length=79, dry_run=False):
    """
    Process all Python files in a directory recursively.

    Args:
        directory: Directory to process
        extension: File extension to filter by
        fix_imports: Whether to fix unused imports
        fix_lines: Whether to fix long lines
        max_length: Maximum allowed line length
        dry_run: If True, don't modify files, just report

    Returns:
        dict: Aggregated statistics
    """
    stats = {'files_processed': 0, 'imports_removed': 0, 'lines_fixed': 0}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(root, file)
                file_stats = process_file(
                    file_path,
                    fix_imports=fix_imports,
                    fix_lines=fix_lines,
                    max_length=max_length,
                    dry_run=dry_run
                )
                stats['files_processed'] += 1
                stats['imports_removed'] += file_stats['imports_removed']
                stats['lines_fixed'] += file_stats['lines_fixed']

    return stats

def main():
    parser = argparse.ArgumentParser(description='Advanced import and style fixer for Python files')
    parser.add_argument('path', help='File or directory to process')
    parser.add_argument('--no-imports', action='store_false', dest='fix_imports',
                        help='Skip fixing unused imports')
    parser.add_argument('--no-lines', action='store_false', dest='fix_lines',
                        help='Skip fixing long lines')
    parser.add_argument('--max-length', type=int, default=79,
                        help='Maximum line length')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be modified without making changes')

    args = parser.parse_args()

    path = args.path

    print(f"Processing {path}...")
    if os.path.isfile(path):
        stats = process_file(
            path,
            fix_imports=args.fix_imports,
            fix_lines=args.fix_lines,
            max_length=args.max_length,
            dry_run=args.dry_run
        )
        print(f"Processed 1 file, removed {stats['imports_removed']} imports, fixed {stats['lines_fixed']} long lines")
    elif os.path.isdir(path):
        stats = process_directory(
            path,
            fix_imports=args.fix_imports,
            fix_lines=args.fix_lines,
            max_length=args.max_length,
            dry_run=args.dry_run
        )
        print(f"Processed {stats['files_processed']} files, removed {stats['imports_removed']} imports, fixed {stats['lines_fixed']} long lines")
    else:
        print(f"Error: {path} is not a valid file or directory")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
