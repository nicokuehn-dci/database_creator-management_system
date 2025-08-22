#!/usr/bin/env python3
"""
Main entry point for running the database creator application.
This file detects if the user has the new modular package installed
and runs either the modular version or the original script.
"""
import os
import sys
import importlib.util

def main():
    """Main entry point that detects which version to run."""
    # Check if this is being run from the package directory with both versions available
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if we're in a directory with both the package and the original script
    package_init = os.path.join(current_dir, "database_creator", "__init__.py")
    original_script = os.path.join(current_dir, "database_creator.py")

    # If we have the modular package structure
    if os.path.exists(package_init):
        try:
            # Try to import and run the modular version
            from database_creator.cli import main as cli_main
            cli_main()
        except ImportError:
            print("Error importing modular version. Falling back to original script.")
            # Fall back to the original script if available
            if os.path.exists(original_script):
                # Use importlib to load the original script
                spec = importlib.util.spec_from_file_location("database_creator_script", original_script)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Run the main function from the original script
                module.main()
            else:
                print("Error: Neither modular package nor original script found.")
                sys.exit(1)
    # If we only have the original script
    elif os.path.exists(original_script):
        # Use importlib to load the original script
        spec = importlib.util.spec_from_file_location("database_creator_script", original_script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Run the main function from the original script
        module.main()
    else:
        print("Error: Database creator files not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
