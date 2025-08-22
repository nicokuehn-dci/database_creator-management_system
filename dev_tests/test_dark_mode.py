"""
Practical test script for launching the GUI with dark mode functionality.
This script simply launches the main application, allowing you to manually
test the dark mode through the Settings menu.
"""
import os
import sys
import tkinter as tk

# Add parent directory to path to import database_creator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_creator.gui import GUI

def run_gui():
    """
    Launch the main GUI for manual testing.

    How to test dark mode:
    1. Use the Settings menu
    2. Toggle "Dark Mode" option on/off
    3. Observe the changes in the interface
    """
    print("Launching Database Creator GUI")
    print("To test dark mode:")
    print("  1. Click on the 'Settings' menu")
    print("  2. Toggle the 'Dark Mode' checkbox")
    print("  3. Observe theme changes throughout the application")
    print("\nPress Ctrl+C in this terminal to exit the application")

    # Initialize the GUI
    root = tk.Tk()
    gui = GUI(root)

    # Run the application
    gui.run()

if __name__ == "__main__":
    try:
        run_gui()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
    except Exception as e:
        print(f"Error running application: {e}")
        import traceback
        traceback.print_exc()
