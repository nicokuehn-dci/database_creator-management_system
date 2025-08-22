
"""
Main entry point for the database creator application.
Automatically checks and installs required dependencies before running.
"""
import sys
import argparse
import subprocess
import importlib
import os
import re

def load_requirements():
    """Load required packages from requirements.txt"""
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.exists(req_file):
        return ["openpyxl", "pymysql", "psycopg2", "pyodbc", "requests",
                "pandas", "matplotlib", "numpy", "seaborn"]

    required = []
    with open(req_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Extract package name (without version)
            package = re.split(r'[<>=~]', line)[0].strip()
            if package:
                required.append(package)
    return required

# Load required packages from requirements.txt
REQUIRED_PACKAGES = load_requirements()

def check_and_install_packages():
    # Check for pip first
    try:
        import pip
    except ImportError:
        print("pip is not installed. Attempting to install pip...")
        try:
            # Use ensurepip if available
            import ensurepip
            ensurepip.bootstrap()
            print("pip installed successfully.")
        except Exception:
            # Try get-pip.py as fallback
            import urllib.request
            import tempfile
            import os
            get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
            with tempfile.TemporaryDirectory() as tmpdir:
                get_pip_path = os.path.join(tmpdir, "get-pip.py")
                try:
                    urllib.request.urlretrieve(get_pip_url, get_pip_path)
                    subprocess.check_call([sys.executable, get_pip_path])
                    print("pip installed successfully via get-pip.py.")
                except Exception as e:
                    print(f"Failed to install pip: {e}")
                    sys.exit(1)

    # Now check for required packages
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"✓ {pkg} is already installed")
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} is not installed")

    if missing:
        print(f"\nInstalling {len(missing)} missing package(s)...")
        for i, pkg in enumerate(missing):
            progress = f"[{i+1}/{len(missing)}]"
            print(f"{progress} Installing {pkg}...", end="", flush=True)
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(" ✓ Success")
                else:
                    print(f" ✗ Failed: {result.stderr.strip()}")
                    print(f"Error installing {pkg}. Please install manually.")
            except Exception as e:
                print(f" ✗ Failed: {str(e)}")
                print(f"Error installing {pkg}. Please install manually.")

# Run dependency check before importing app modules
check_and_install_packages()

from database_creator.cli import CLI
# Import GUI later to avoid circular imports

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Database Creator - Create and manage SQLite databases'
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch with graphical user interface'
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Launch with command line interface (default)'
    )
    parser.add_argument(
        '--db',
        help='Database file path'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )
    parser.add_argument(
        '--diagnostic',
        action='store_true',
        help='Run system diagnostic and display results'
    )
    parser.add_argument(
        '--check-db',
        metavar='DB_PATH',
        help='Check health of a specific database file'
    )
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()

    # Show version info and exit if requested
    if args.version:
        from database_creator import __version__
        print(f"Database Creator v{__version__}")
        sys.exit(0)

    # Run diagnostic if requested
    if args.diagnostic:
        from database_creator.diagnostics import run_diagnostic
        print("Running system diagnostic...")
        result = run_diagnostic()
        print("\n=== System Information ===")
        for key, value in result["system_info"].items():
            print(f"{key}: {value}")

        print("\n=== Package Versions ===")
        for pkg, version in result["package_versions"].items():
            print(f"{pkg}: {version}")

        print("\n=== Config Information ===")
        print(f"Config exists: {result['config_exists']}")
        print(f"Config valid: {result.get('config_valid', False)}")
        if 'config_keys' in result:
            print(f"Config keys: {', '.join(result['config_keys'])}")

        print("\n=== Database Information ===")
        print(f"Storage directory exists: {result['storage_dir_exists']}")
        if 'database_count' in result:
            print(f"Database count: {result['database_count']}")
            print(f"Databases: {', '.join(result['databases'])}")
        sys.exit(0)

    # Check specific database if requested
    if args.check_db:
        from database_creator.diagnostics import check_database_health
        print(f"Checking database: {args.check_db}")
        result = check_database_health(args.check_db)
        if result["status"] == "error":
            print(f"Error: {result['message']}")
            sys.exit(1)
        else:
            print("\n=== Database Health ===")
            print(f"Integrity: {result['integrity']}")
            print(f"Size: {result['size_mb']} MB")
            print(f"Tables: {', '.join(result['tables'])}")
            print(f"Table count: {result['table_count']}")
            sys.exit(0)

    # Determine interface mode
    use_gui = args.gui or (not args.cli and not sys.argv[1:])

    if use_gui:
        try:
            # Import GUI modules here to avoid circular imports
            import tkinter as tk
            from database_creator.gui import GUI

            # Launch GUI
            root = tk.Tk()
            gui = GUI(root)

            # Connect to specified database if provided
            if args.db:
                gui.connect_database(args.db)

            gui.run()
        except Exception as e:
            print(f"Error launching GUI: {e}")
            print("Falling back to CLI mode...")
            use_gui = False

    if not use_gui:
        # Launch CLI
        cli = CLI()

        # If a DB path was specified, override sys.argv for CLI parsing
        if args.db:
            db_arg = f"--db={args.db}"
            filtered_args = [arg for arg in sys.argv[1:]
                           if not arg.startswith('--db=') and arg != '--cli']
            sys.argv = [sys.argv[0], db_arg] + filtered_args

        cli.run()

if __name__ == "__main__":
    main()
