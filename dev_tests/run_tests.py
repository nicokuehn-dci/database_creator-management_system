"""
Main test runner script for the database_creator package.
Run this script to execute all tests in the dev_tests directory.
"""
import os
import sys
import subprocess

def run_automated_tests():
    """Run all automated tests in the dev_tests directory."""
    print("=" * 80)
    print("Running Database Creator Automated Tests")
    print("=" * 80)

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Functionality tests
    print("\nRunning functionality tests:")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-xvs", "test_functionality.py"],
            cwd=current_dir,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running functionality tests: {e}")

    # GUI tests
    print("\nRunning GUI tests:")
    try:
        result = subprocess.run(
            ["python", "test_gui.py"],
            cwd=current_dir,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running GUI tests: {e}")

    print("\n" + "=" * 80)
    print("Tests completed")
    print("=" * 80)

def run_gui_test():
    """Launch the GUI for manual testing."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Run the dark mode test script which launches the GUI
    subprocess.run(
        ["python", "test_dark_mode.py"],
        cwd=current_dir,
        check=False
    )

def show_menu():
    """Show the main menu for test selection."""
    print("\n" + "=" * 80)
    print("Database Creator Test Suite")
    print("=" * 80)
    print("1. Run Automated Tests (Unit Tests)")
    print("2. Launch GUI for Manual Testing")
    print("3. Exit")

    choice = input("\nEnter your choice (1-3): ")

    if choice == "1":
        run_automated_tests()
    elif choice == "2":
        run_gui_test()
    elif choice == "3":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\nTests canceled by user")
        sys.exit(1)
