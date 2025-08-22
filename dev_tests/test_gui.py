import tkinter as tk
import sys
import os

# Add parent directory to path to import database_creator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_creator.gui import GUI

def test_gui_initialization():
    """Test initialization of the GUI."""
    # Try to initialize the GUI
    try:
        root = tk.Tk()
        gui = GUI(root)
        print("GUI initialized successfully")

        # Test theme toggle functionality
        print("Testing light theme...")
        gui.dark_mode.set(False)
        gui.toggle_theme()

        print("Testing dark theme...")
        gui.dark_mode.set(True)
        gui.toggle_theme()

        # Clean up
        root.after(2000, root.destroy)
        root.mainloop()

        return True
    except Exception as e:
        print(f"Error initializing GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gui_initialization()
