#!/usr/bin/env python3
"""
Final fix script for Database Creator package.
"""

import os
import re
import sys

def fix_unused_imports(content):
    """Remove unused imports."""
    # Remove unused imports
    content = re.sub(r'from tkinter import ([^,]*),\s*simpledialog([^,]*)',
                     r'from tkinter import \1\2', content)

    # Remove typing imports completely
    content = re.sub(r'from typing import[^\n]*\n', '', content)

    # Remove hash_password import
    content = re.sub(r'from \.security import hash_password\n', '', content)

    return content

def fix_long_lines(content, max_length=79):
    """Fix long lines in a way that doesn't break syntax."""
    lines = content.split('\n')
    result_lines = []

    for line in lines:
        if len(line) <= max_length or line.strip().startswith('#') or '"""' in line:
            result_lines.append(line)
            continue

        # Fix long function calls
        if '(' in line and ')' in line and ',' in line:
            # Handle function call with parameters
            indent = len(line) - len(line.lstrip())
            function_name_end = line.find('(')

            if function_name_end > 0 and function_name_end < max_length - 10:
                prefix = line[:function_name_end + 1]
                remainder = line[function_name_end + 1:]

                # Close parentheses needs special handling
                if remainder.rstrip().endswith(')'):
                    params = remainder.rstrip()[:-1]  # remove closing parenthesis
                    params_parts = params.split(',')

                    # Add first line
                    result_lines.append(prefix)

                    # Add parameters
                    for i, part in enumerate(params_parts):
                        part = part.strip()
                        if i < len(params_parts) - 1:
                            result_lines.append(' ' * (indent + 4) + part + ',')
                        else:
                            result_lines.append(' ' * (indent + 4) + part + ')')

                    continue

        # Fix long string assignments
        if ' = ' in line and ('"' in line or "'" in line):
            parts = line.split(' = ', 1)
            if len(parts[0]) < max_length - 10:
                result_lines.append(parts[0] + ' = \\')
                result_lines.append(' ' * (len(parts[0]) + 3) + parts[1])
                continue

        # If we couldn't fix it, just add the original line
        result_lines.append(line)

    return '\n'.join(result_lines)

def fix_f_string_placeholders(content):
    """Fix f-strings that are missing placeholders."""
    lines = content.split('\n')
    result = []

    for line in lines:
        # Check if there's an f-string without placeholders
        if 'f"' in line and '{' not in line:
            line = line.replace('f"', '"')
        if "f'" in line and '{' not in line:
            line = line.replace("f'", "'")

        result.append(line)

    return '\n'.join(result)

def fix_bare_except(content):
    """Replace bare excepts with Exception."""
    return content.replace('except:', 'except Exception:')

def fix_file(filepath):
    """Apply all fixes to the file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply fixes
    content = fix_unused_imports(content)
    content = fix_long_lines(content)
    content = fix_f_string_placeholders(content)
    content = fix_bare_except(content)

    # Write the changes back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fixed {filepath}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python final_fix.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} does not exist")
        sys.exit(1)

    fix_file(filepath)
    return 0

if __name__ == "__main__":
    sys.exit(main())
