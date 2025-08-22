#!/usr/bin/env python3
"""
Debug script to test the database_creator package.
"""
import os
import sys

# Add the current directory to sys.path
sys.path.insert(0, os.path.abspath('.'))

try:
    print("Attempting to import database_creator package...")
    import database_creator
    print(f"Success! Found database_creator package version: {database_creator.__version__}")

    # Test importing the modules
    print("\nTesting imports from each module:")
    try:
        from database_creator.database import DatabaseManager
        print("✓ DatabaseManager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import DatabaseManager: {e}")

    try:
        from database_creator.templates import DatabaseTemplates
        print("✓ DatabaseTemplates imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import DatabaseTemplates: {e}")

    try:
        from database_creator.security import hash_password
        print("✓ hash_password imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import hash_password: {e}")

    try:
        from database_creator.cli import CLI
        print("✓ CLI imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import CLI: {e}")

    try:
        from database_creator.gui import GUI
        print("✓ GUI imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import GUI: {e}")

except ImportError as e:
    print(f"Failed to import database_creator package: {e}")

    # Check if the package directory exists
    package_dir = os.path.join(os.path.abspath('.'), 'database_creator')
    print(f"\nChecking for package directory: {package_dir}")
    if os.path.exists(package_dir):
        print("✓ Package directory exists")

        # Check for __init__.py
        init_py = os.path.join(package_dir, '__init__.py')
        if os.path.exists(init_py):
            print("✓ __init__.py exists")

            # List files in the package directory
            print("\nFiles in package directory:")
            for file in os.listdir(package_dir):
                print(f"- {file}")
        else:
            print("✗ __init__.py missing!")
    else:
        print("✗ Package directory missing!")
