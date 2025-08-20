"""
Main entry point for the database creator application.
"""
import sys
import argparse
from database_creator.cli import CLI
from database_creator.gui import GUI


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
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Show version info and exit if requested
    if args.version:
        from database_creator import __version__
        print(f"Database Creator v{__version__}")
        sys.exit(0)
    
    # Determine interface mode
    use_gui = args.gui or (not args.cli and not sys.argv[1:])
    
    if use_gui:
        try:
            # Launch GUI
            gui = GUI()
            
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
