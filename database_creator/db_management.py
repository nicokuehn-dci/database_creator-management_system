"""
Database management module for the Database Creator application.
This module provides the UI and functionality for the database management tab.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sqlite3
import datetime
import shutil
import re

from .config import DB_STORAGE_DIR, ensure_directory_exists, load_config
from .db_connections import DatabaseConnection
from .db_utils import DatabaseUtils
from .db_table_manager import DatabaseTableManager
from .db_import_export import DatabaseImportExport

class DatabaseManagementTab:
    def __init__(self, parent, main_app):
        """
        Initialize the database management tab.

        Args:
            parent: The parent notebook widget
            main_app: The main application instance
        """
        self.parent = parent
        self.main_app = main_app
        self.tab = ttk.Frame(parent)

        # Ensure database storage directory exists
        ensure_directory_exists(DB_STORAGE_DIR)

        # Create the main layout
        self.create_layout()

        # Refresh the database list
        self.refresh_db_list()

    def create_layout(self):
        """Create the layout for the database management tab"""
        # Create main frames for left sidebar and right content
        left_frame = ttk.Frame(self.tab, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False,
                      padx=10, pady=10)
        left_frame.pack_propagate(False)  # Maintain width

        right_frame = ttk.Frame(self.tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True,
                       padx=10, pady=10)

        # Left frame - Database list and actions
        list_label = ttk.Label(left_frame, text="Databases:", font=("Arial", 12))
        list_label.pack(anchor="w", pady=(0, 5))

        # Create a frame for buttons
        action_frame = ttk.Frame(left_frame)
        action_frame.pack(fill=tk.X, pady=10)

        # Create New Database button
        create_btn = ttk.Button(
            action_frame,
            text="Create New Database",
            command=self.create_new_database
        )
        create_btn.pack(fill=tk.X, pady=2)

        # Create New Database tooltip
        create_tooltip = ttk.Label(
            action_frame,
            text="Create a new SQLite database and\nsave it to the database folder",
            foreground="gray"
        )
        create_tooltip.pack(fill=tk.X, pady=(0, 5))

        # Open Database button
        open_btn = ttk.Button(
            action_frame,
            text="Open Existing Database",
            command=self.open_database_dialog
        )
        open_btn.pack(fill=tk.X, pady=2)

        # Open Database tooltip
        open_tooltip = ttk.Label(
            action_frame,
            text="Open an existing database from the\ndatabase folder or any location",
            foreground="gray"
        )
        open_tooltip.pack(fill=tk.X, pady=(0, 5))

        # Connect to External Database button
        connect_btn = ttk.Button(
            action_frame,
            text="Connect to External DB",
            command=self.connect_external_db
        )
        connect_btn.pack(fill=tk.X, pady=2)

        # Connect to External Database tooltip
        connect_tooltip = ttk.Label(
            action_frame,
            text="Connect to external MySQL, PostgreSQL\nor remote databases",
            foreground="gray"
        )
        connect_tooltip.pack(fill=tk.X, pady=(0, 5))

        # Search and filter frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=2)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_database_list)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Sort options
        sort_frame = ttk.Frame(left_frame)
        sort_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT, padx=2)

        self.sort_option = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_option,
                                width=10, state="readonly")
        sort_combo.pack(side=tk.LEFT, padx=2)
        sort_combo['values'] = ["Name", "Size", "Modified"]
        sort_combo.bind("<<ComboboxSelected>>", self.sort_database_list)

        self.sort_descending = tk.BooleanVar(value=False)
        sort_order_btn = ttk.Checkbutton(
            sort_frame,
            text="Descending",
            variable=self.sort_descending,
            command=self.sort_database_list
        )
        sort_order_btn.pack(side=tk.LEFT, padx=2)

        # Refresh button
        refresh_btn = ttk.Button(
            action_frame,
            text="Refresh List",
            command=self.refresh_db_list
        )
        refresh_btn.pack(fill=tk.X, pady=2)

        # Database listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.db_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.db_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.db_listbox.bind('<Double-1>', self.on_db_select)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                command=self.db_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.db_listbox.config(yscrollcommand=scrollbar.set)

        # Right frame - Database info and preview
        self.info_frame = ttk.LabelFrame(right_frame, text="Database Information")
        self.info_frame.pack(fill=tk.X, pady=10)

        # Database info
        self.db_name_var = tk.StringVar(value="No database selected")
        self.db_path_var = tk.StringVar(value="")
        self.db_size_var = tk.StringVar(value="")
        self.db_tables_var = tk.StringVar(value="")
        self.db_modified_var = tk.StringVar(value="")

        info_grid = ttk.Frame(self.info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=5)

        # Database name
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(info_grid, textvariable=self.db_name_var).grid(
            row=0, column=1, sticky="w", pady=2)

        # Database path
        ttk.Label(info_grid, text="Path:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(info_grid, textvariable=self.db_path_var).grid(
            row=1, column=1, sticky="w", pady=2)

        # Database size
        ttk.Label(info_grid, text="Size:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(info_grid, textvariable=self.db_size_var).grid(
            row=2, column=1, sticky="w", pady=2)

        # Database tables
        ttk.Label(info_grid, text="Tables:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Label(info_grid, textvariable=self.db_tables_var).grid(
            row=3, column=1, sticky="w", pady=2)

        # Last modified
        ttk.Label(info_grid, text="Modified:").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Label(info_grid, textvariable=self.db_modified_var).grid(
            row=4, column=1, sticky="w", pady=2)

        # Table preview frame
        self.preview_frame = ttk.LabelFrame(right_frame, text="Database Tables")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Table selector
        table_select_frame = ttk.Frame(self.preview_frame)
        table_select_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(table_select_frame, text="Select Table:").pack(side=tk.LEFT, padx=5)

        self.table_combobox = ttk.Combobox(table_select_frame, state="readonly")
        self.table_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.table_combobox.bind("<<ComboboxSelected>>", self.on_table_selected)

        # Table data treeview
        self.tree_frame = ttk.Frame(self.preview_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.treeview = ttk.Treeview(self.tree_frame)
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scrolly = ttk.Scrollbar(self.tree_frame, orient="vertical",
                                   command=self.treeview.yview)
        tree_scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        self.treeview.configure(yscrollcommand=tree_scrolly.set)

        tree_scrollx = ttk.Scrollbar(self.preview_frame, orient="horizontal",
                                   command=self.treeview.xview)
        tree_scrollx.pack(fill=tk.X)
        self.treeview.configure(xscrollcommand=tree_scrollx.set)

        # Table data operations
        data_ops_frame = ttk.Frame(self.preview_frame)
        data_ops_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            data_ops_frame,
            text="Edit Row",
            command=self.edit_selected_row
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            data_ops_frame,
            text="Add Row",
            command=self.add_new_row
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            data_ops_frame,
            text="Delete Row",
            command=self.delete_selected_row
        ).pack(side=tk.LEFT, padx=2)

        # Search within table
        table_search_frame = ttk.Frame(self.preview_frame)
        table_search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(table_search_frame, text="Search Table:").pack(side=tk.LEFT, padx=2)

        self.table_search_var = tk.StringVar()
        self.table_search_var.trace_add("write", self.search_in_table)

        table_search_entry = ttk.Entry(
            table_search_frame,
            textvariable=self.table_search_var
        )
        table_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Database actions
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X, pady=5)

        self.open_btn = ttk.Button(
            actions_frame,
            text="Open Selected Database",
            command=self.open_selected_database
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)

        self.delete_btn = ttk.Button(
            actions_frame,
            text="Delete Selected Database",
            command=self.delete_selected_database
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        # Export/Import buttons
        ttk.Button(
            actions_frame,
            text="Export Data",
            command=self.export_database_data
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="Clone Database",
            command=self.clone_database
        ).pack(side=tk.LEFT, padx=5)

        # Disable buttons initially
        self.open_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)

    def refresh_db_list(self):
        """Refresh the list of databases in the storage directory"""
        self.db_listbox.delete(0, tk.END)

        # Ensure the directory exists
        ensure_directory_exists(DB_STORAGE_DIR)

        # List all .db files in the directory
        self.db_files = []
        if os.path.exists(DB_STORAGE_DIR):
            self.db_files = [f for f in os.listdir(DB_STORAGE_DIR)
                        if f.endswith('.db') and os.path.isfile(
                            os.path.join(DB_STORAGE_DIR, f))]

        # Add external database connections from config
        config = load_config()
        external_connections = config.get("external_connections", {})

        # Add them to the list with a special prefix
        for conn_name in external_connections:
            self.db_files.append(f"[EXTERNAL] {conn_name}")

        # Apply any filtering and sorting
        self.apply_filters_and_sorting()

    def filter_database_list(self, *args):
        """Filter the database list based on search text"""
        self.apply_filters_and_sorting()

    def sort_database_list(self, *args):
        """Sort the database list based on selected criteria"""
        self.apply_filters_and_sorting()

    def apply_filters_and_sorting(self):
        """Apply filtering and sorting to the database list"""
        # Clear the list
        self.db_listbox.delete(0, tk.END)

        # Start with all files
        filtered_files = self.db_files.copy()

        # Apply search filter if any
        search_text = self.search_var.get().lower()
        if search_text:
            filtered_files = [f for f in filtered_files
                             if search_text in f.lower()]

        # Apply sorting
        sort_option = self.sort_option.get().lower()
        reverse = self.sort_descending.get()

        if sort_option == "name":
            # Sort by name (default)
            filtered_files.sort(reverse=reverse)
        elif sort_option == "size":
            # Sort by file size
            filtered_files.sort(
                key=lambda f: os.path.getsize(os.path.join(DB_STORAGE_DIR, f)),
                reverse=reverse
            )
        elif sort_option == "modified":
            # Sort by modification time
            filtered_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(DB_STORAGE_DIR, f)),
                reverse=reverse
            )

        # Update the listbox
        for db_file in filtered_files:
            self.db_listbox.insert(tk.END, db_file)

    def on_db_select(self, _event=None):
        """Handle database selection from the listbox"""
        selection = self.db_listbox.curselection()
        if not selection:
            return

        db_name = self.db_listbox.get(selection[0])
        db_path = os.path.join(DB_STORAGE_DIR, db_name)

        self.show_db_info(db_path)
        self.open_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)

    def show_db_info(self, db_path):
        """Show information about the selected database"""
        if not os.path.exists(db_path):
            messagebox.showerror("Error", f"Database file not found: {db_path}")
            return

        try:
            # Get basic file info
            file_size = os.path.getsize(db_path)
            file_size_readable = DatabaseUtils.format_file_size(file_size)

            modified_time = os.path.getmtime(db_path)
            modified_date = datetime.datetime.fromtimestamp(
                modified_time).strftime('%Y-%m-%d %H:%M:%S')

            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables if table[0] != 'sqlite_sequence']

            # Update UI elements
            self.db_name_var.set(os.path.basename(db_path))
            self.db_path_var.set(db_path)
            self.db_size_var.set(file_size_readable)
            self.db_tables_var.set(f"{len(table_names)} tables")
            self.db_modified_var.set(modified_date)

            # Update table combobox
            self.table_combobox['values'] = table_names
            if table_names:
                self.table_combobox.current(0)
                self.on_table_selected()
            else:
                # Clear treeview if no tables
                self.clear_treeview()

            conn.close()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error accessing database: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def on_table_selected(self, _event=None):
        """Display data for the selected table"""
        selected_table = self.table_combobox.get()
        if not selected_table:
            return

        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            return

        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get column names
            cursor.execute(f"PRAGMA table_info('{selected_table}')")
            columns = [column[1] for column in cursor.fetchall()]

            # Get data (limit to 100 rows for performance)
            cursor.execute(f"SELECT * FROM '{selected_table}' LIMIT 100")
            data = cursor.fetchall()

            # Update treeview
            self.update_treeview(columns, data)

            conn.close()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error accessing table: {e}")

    def update_treeview(self, columns, data):
        """Update the treeview with the given columns and data"""
        # Clear existing data
        self.clear_treeview()

        # Set up columns
        self.treeview['columns'] = columns
        self.treeview.column('#0', width=0, stretch=tk.NO)

        for col in columns:
            self.treeview.column(col, anchor=tk.W, width=100)
            self.treeview.heading(col, text=col, anchor=tk.W)

        # Insert data
        for i, row in enumerate(data):
            self.treeview.insert('', tk.END, text=str(i), values=row)

    def clear_treeview(self):
        """Clear all items in the treeview"""
        self.treeview.delete(*self.treeview.get_children())

        # Remove all columns
        self.treeview['columns'] = ()

    # Method removed: Using DatabaseUtils.format_file_size() instead

    def create_new_database(self):
        """Create a new database file"""
        # Ask for database name
        db_name = filedialog.asksaveasfilename(
            title="Create New Database",
            initialdir=DB_STORAGE_DIR,
            filetypes=[("SQLite Database", "*.db")],
            defaultextension=".db"
        )

        if not db_name:
            return  # User cancelled

        # If user selected a location outside the storage dir, copy it
        if not db_name.startswith(DB_STORAGE_DIR):
            original_path = db_name
            filename = os.path.basename(original_path)
            db_name = os.path.join(DB_STORAGE_DIR, filename)

        try:
            # Create an empty database
            conn = sqlite3.connect(db_name)
            conn.close()

            messagebox.showinfo("Success",
                              f"Database '{os.path.basename(db_name)}' created successfully")

            # Refresh the database list and select the new database
            self.refresh_db_list()

            # Open the database in the main application
            if hasattr(self.main_app, 'set_current_database'):
                self.main_app.set_current_database(db_name)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create database: {e}")

    def open_database_dialog(self):
        """Open a dialog to select a database file"""
        db_path = filedialog.askopenfilename(
            title="Open Database",
            initialdir=DB_STORAGE_DIR,
            filetypes=[("SQLite Database", "*.db")]
        )

        if not db_path:
            return  # User cancelled

        # If database is outside storage dir, offer to copy it
        if not db_path.startswith(DB_STORAGE_DIR):
            copy_to_storage = messagebox.askyesno(
                "Copy to Storage",
                "Would you like to copy this database to the database storage folder?"
            )

            if copy_to_storage:
                filename = os.path.basename(db_path)
                new_path = os.path.join(DB_STORAGE_DIR, filename)

                # Check if file already exists
                if os.path.exists(new_path):
                    overwrite = messagebox.askyesno(
                        "Overwrite",
                        f"A file named '{filename}' already exists in the storage folder. Overwrite it?"
                    )

                    if not overwrite:
                        return

                try:
                    # Copy the file
                    shutil.copy2(db_path, new_path)
                    db_path = new_path
                    messagebox.showinfo("Success",
                                      f"Database copied to storage folder as '{filename}'")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy database: {e}")

        # Open the database in the main application
        if hasattr(self.main_app, 'set_current_database'):
            self.main_app.set_current_database(db_path)

        self.refresh_db_list()

    def open_selected_database(self):
        """Open the currently selected database in the main app"""
        selection = self.db_listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "Please select a database first")
            return

        db_name = self.db_listbox.get(selection[0])
        db_path = os.path.join(DB_STORAGE_DIR, db_name)

        if not os.path.exists(db_path):
            messagebox.showerror("Error", f"Database file not found: {db_path}")
            self.refresh_db_list()  # Refresh the list to remove non-existent files
            return

        # Open the database in the main application
        if hasattr(self.main_app, 'set_current_database'):
            self.main_app.set_current_database(db_path)
        else:
            messagebox.showinfo("Information",
                              "Database selected: " + db_name)

    def delete_selected_database(self):
        """Delete the currently selected database"""
        selection = self.db_listbox.curselection()
        if not selection:
            messagebox.showinfo("Information", "Please select a database first")
            return

        db_name = self.db_listbox.get(selection[0])
        db_path = os.path.join(DB_STORAGE_DIR, db_name)

        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the database '{db_name}'?\n\n"
            "This action cannot be undone."
        )

        if not confirm:
            return

        try:
            # Close database if it's currently open in the app
            if hasattr(self.main_app, 'current_db') and \
               self.main_app.current_db == db_path:
                # Reset current database if possible
                if hasattr(self.main_app, 'set_current_database'):
                    self.main_app.set_current_database(None)

            # Delete the file
            os.remove(db_path)
            messagebox.showinfo("Success", f"Database '{db_name}' deleted successfully")

            # Refresh the list and clear info
            self.refresh_db_list()
            self.clear_db_info()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete database: {e}")

    def clear_db_info(self):
        """Clear the database information display"""
        self.db_name_var.set("No database selected")
        self.db_path_var.set("")
        self.db_size_var.set("")
        self.db_tables_var.set("")
        self.db_modified_var.set("")

        # Clear table combobox
        self.table_combobox['values'] = []

        # Clear treeview
        self.clear_treeview()

        # Clear table search
        if hasattr(self, 'table_search_var'):
            self.table_search_var.set("")

        # Disable buttons
        self.open_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)

    def edit_selected_row(self):
        """Edit the selected row in the current table view"""
        selected_items = self.treeview.selection()
        if not selected_items:
            messagebox.showinfo("Information", "Please select a row to edit")
            return

        # Get the current table
        table_name = self.table_combobox.get()
        if not table_name:
            return

        # Get the database path
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            return

        # Get the selected row data
        item_id = selected_items[0]
        values = self.treeview.item(item_id, 'values')

        # Get column names
        columns = self.treeview['columns']

        # Create edit dialog
        self.create_edit_dialog(table_name, columns, values, is_new=False)

    def add_new_row(self):
        """Add a new row to the current table"""
        # Get the current table
        table_name = self.table_combobox.get()
        if not table_name:
            messagebox.showinfo("Information", "Please select a table first")
            return

        # Get the database path
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            return

        # Get column names
        columns = self.treeview['columns']

        # Create empty values
        values = [""] * len(columns)

        # Create edit dialog
        self.create_edit_dialog(table_name, columns, values, is_new=True)

    def create_edit_dialog(self, table_name, columns, values, is_new=False):
        """Create a dialog for editing or adding rows"""
        dialog = tk.Toplevel(self.tab)
        title = "Add New Row" if is_new else "Edit Row"
        dialog.title(f"{title} - {table_name}")
        dialog.geometry("500x400")
        dialog.transient(self.tab)
        dialog.grab_set()

        # Create scrollable frame
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create entry fields for each column
        entries = []
        for i, (col, val) in enumerate(zip(columns, values)):
            frame = ttk.Frame(scroll_frame)
            frame.pack(fill=tk.X, pady=5)

            ttk.Label(frame, text=f"{col}:").pack(side=tk.LEFT, padx=5)
            entry = ttk.Entry(frame, width=40)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            # Set value if exists
            if val is not None:
                entry.insert(0, str(val))

            entries.append(entry)

        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_data():
            # Collect values from entries
            new_values = [entry.get() for entry in entries]

            # Save to database
            db_path = self.db_path_var.get()

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                if is_new:
                    # Create INSERT statement
                    placeholders = ", ".join(["?"] * len(columns))
                    cols = ", ".join(columns)
                    sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
                    cursor.execute(sql, new_values)
                else:
                    # Create UPDATE statement - assume first value is ID
                    set_clause = ", ".join([f"{col} = ?" for col in columns[1:]])
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {columns[0]} = ?"

                    # Rearrange values: move first value to the end for WHERE clause
                    update_values = new_values[1:] + [new_values[0]]
                    cursor.execute(sql, update_values)

                conn.commit()
                conn.close()

                # Update display
                self.on_table_selected()
                dialog.destroy()

                action = "added" if is_new else "updated"
                messagebox.showinfo("Success", f"Row {action} successfully")

            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))

        ttk.Button(btn_frame, text="Save", command=save_data).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.RIGHT, padx=5
        )

    def delete_selected_row(self):
        """Delete the selected row from the current table"""
        selected_items = self.treeview.selection()
        if not selected_items:
            messagebox.showinfo("Information", "Please select a row to delete")
            return

        # Get the current table
        table_name = self.table_combobox.get()
        if not table_name:
            return

        # Get the database path
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            return

        # Get the selected row data
        item_id = selected_items[0]
        values = self.treeview.item(item_id, 'values')

        if not values:
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this row?\n\n"
            "This action cannot be undone."
        )

        if not confirm:
            return

        try:
            # Assume first column is the primary key
            primary_key_col = self.treeview['columns'][0]
            primary_key_val = values[0]

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Delete the row
            sql = f"DELETE FROM {table_name} WHERE {primary_key_col} = ?"
            cursor.execute(sql, (primary_key_val,))

            conn.commit()
            conn.close()

            # Update display
            self.on_table_selected()

            messagebox.showinfo("Success", "Row deleted successfully")

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    def search_in_table(self, *args):
        """Search within the current table view"""
        search_text = self.table_search_var.get().lower()

        # If no search text, show all rows
        if not search_text:
            self.on_table_selected()
            return

        # Get the current table
        table_name = self.table_combobox.get()
        if not table_name:
            return

        # Get the database path
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get column names
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = [column[1] for column in cursor.fetchall()]

            # Create WHERE clause for each column (case-insensitive search)
            where_clauses = [
                f"LOWER({col}) LIKE ?" for col in columns
            ]
            where_clause = " OR ".join(where_clauses)

            # Create parameters
            params = [f"%{search_text}%" for _ in columns]

            # Execute the query
            cursor.execute(
                f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 100",
                params
            )
            data = cursor.fetchall()

            # Update treeview
            self.update_treeview(columns, data)

            conn.close()

        except sqlite3.Error as e:
            messagebox.showerror("Search Error", str(e))

    def export_database_data(self):
        """Export the current database to various formats"""
        # Get the database path
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            messagebox.showinfo("Information", "Please select a database first")
            return

        # Create dialog
        dialog = tk.Toplevel(self.tab)
        dialog.title("Export Database")
        dialog.geometry("400x300")
        dialog.transient(self.tab)
        dialog.grab_set()

        # Format selection
        format_frame = ttk.LabelFrame(dialog, text="Export Format")
        format_frame.pack(fill=tk.X, padx=10, pady=10)

        export_format = tk.StringVar(value="sql")
        ttk.Radiobutton(
            format_frame, text="SQL Script", value="sql", variable=export_format
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            format_frame, text="CSV Files (one per table)",
            value="csv", variable=export_format
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            format_frame, text="JSON", value="json", variable=export_format
        ).pack(anchor=tk.W, padx=10, pady=5)

        # Options frame
        options_frame = ttk.LabelFrame(dialog, text="Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        include_schema = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Include schema (table definitions)",
            variable=include_schema
        ).pack(anchor=tk.W, padx=10, pady=5)

        include_data = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Include data", variable=include_data
        ).pack(anchor=tk.W, padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def export_data():
            fmt = export_format.get()
            schema = include_schema.get()
            data = include_data.get()

            if not schema and not data:
                messagebox.showinfo(
                    "Information",
                    "Please select at least one option (schema or data)"
                )
                return

            # Choose output file/directory
            if fmt == "csv":
                # For CSV, select a directory
                output_path = filedialog.askdirectory(
                    title="Select Directory for CSV Files"
                )
                if not output_path:
                    return
            else:
                # For SQL and JSON, select a file
                extension = "." + fmt
                output_path = filedialog.asksaveasfilename(
                    title=f"Save as {fmt.upper()} File",
                    defaultextension=extension,
                    filetypes=[(f"{fmt.upper()} File", f"*{extension}")]
                )
                if not output_path:
                    return

            try:
                # Call appropriate export function
                if fmt == "sql":
                    self.export_to_sql(db_path, output_path, schema, data)
                elif fmt == "csv":
                    self.export_to_csv(db_path, output_path)
                elif fmt == "json":
                    self.export_to_json(db_path, output_path, schema, data)

                messagebox.showinfo(
                    "Success",
                    f"Database exported successfully to {fmt.upper()} format"
                )
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Export Error", str(e))

        ttk.Button(btn_frame, text="Export", command=export_data).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.RIGHT, padx=5
        )

    def export_to_sql(self, db_path, output_path, include_schema, include_data):
        """Export database to SQL format"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- SQL export from Database Creator\n")
            f.write(f"-- Generated: {datetime.datetime.now()}\n\n")

            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = cursor.fetchall()

            for table_row in tables:
                table_name = table_row[0]

                # Skip SQLite internal tables
                if table_name.startswith('sqlite_'):
                    continue

                if include_schema:
                    # Get CREATE TABLE statement
                    cursor.execute(
                        f"SELECT sql FROM sqlite_master WHERE name='{table_name}'"
                    )
                    create_stmt = cursor.fetchone()[0]
                    f.write(f"{create_stmt};\n\n")

                if include_data:
                    # Get all rows
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()

                    if rows:
                        # Get column names
                        cursor.execute(f"PRAGMA table_info('{table_name}')")
                        columns = [column[1] for column in cursor.fetchall()]

                        for row in rows:
                            # Properly format values
                            values = []
                            for val in row:
                                if val is None:
                                    values.append("NULL")
                                elif isinstance(val, str):
                                    values.append(f"'{val.replace('\'', '\'\'')}'")
                                else:
                                    values.append(str(val))

                            f.write(
                                f"INSERT INTO {table_name} "
                                f"({', '.join(columns)}) "
                                f"VALUES ({', '.join(values)});\n"
                            )
                        f.write("\n")

        conn.close()

    def export_to_csv(self, db_path, output_dir):
        """Export database tables to CSV files (one per table)"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        import csv

        for table_row in tables:
            table_name = table_row[0]

            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue

            # Output file for this table
            output_file = os.path.join(output_dir, f"{table_name}.csv")

            # Get column names
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = [column[1] for column in cursor.fetchall()]

            # Get all rows
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Write CSV file
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)

        conn.close()

    def export_to_json(self, db_path, output_path, include_schema, include_data):
        """Export database to JSON format"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        export_data = {
            "database": os.path.basename(db_path),
            "created": datetime.datetime.now().isoformat(),
            "tables": {}
        }

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table_row in tables:
            table_name = table_row[0]

            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue

            export_data["tables"][table_name] = {}

            if include_schema:
                # Get schema information
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns = []
                for col in cursor.fetchall():
                    columns.append({
                        "name": col[1],
                        "type": col[2],
                        "notnull": col[3] == 1,
                        "default": col[4],
                        "pk": col[5] == 1
                    })
                export_data["tables"][table_name]["schema"] = columns

            if include_data:
                # Get data
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                if rows:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info('{table_name}')")
                    column_names = [column[1] for column in cursor.fetchall()]

                    # Format data as list of dictionaries
                    formatted_rows = []
                    for row in rows:
                        formatted_rows.append(
                            {col: val for col, val in zip(column_names, row)}
                        )
                    export_data["tables"][table_name]["data"] = formatted_rows

        conn.close()

        # Write JSON file
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

    def clone_database(self):
        """Clone the current database to a new file"""
        # Get the current database path
        db_path = self.db_path_var.get()
        if not db_path or not os.path.exists(db_path):
            messagebox.showinfo("Information", "Please select a database first")
            return

        # Get original filename
        original_name = os.path.basename(db_path)
        name_without_ext = os.path.splitext(original_name)[0]

        # Ask for new name
        new_name = simpledialog.askstring(
            "Clone Database",
            "Enter name for the new database:",
            initialvalue=f"{name_without_ext}_copy.db"
        )

        if not new_name:
            return

        # Ensure it has .db extension
        if not new_name.lower().endswith(".db"):
            new_name += ".db"

        # Full path for new database
        new_path = os.path.join(DB_STORAGE_DIR, new_name)

        # Check if file already exists
        if os.path.exists(new_path):
            overwrite = messagebox.askyesno(
                "File Exists",
                f"File '{new_name}' already exists. Overwrite?"
            )
            if not overwrite:
                return

        try:
            # Copy the database file
            shutil.copy2(db_path, new_path)

            messagebox.showinfo(
                "Success",
                f"Database cloned successfully as '{new_name}'"
            )

            # Refresh the database list
            self.refresh_db_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to clone database: {str(e)}")

    def connect_external_db(self):
        """Connect to an external database"""
        # Create connection dialog
        dialog = tk.Toplevel(self.tab)
        dialog.title("Connect to External Database")
        dialog.geometry("500x400")
        dialog.transient(self.tab)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Database type selection
        ttk.Label(main_frame, text="Database Type:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        # Get available database types
        db_types = []
        for db_type, info in ExternalDBConnector.SUPPORTED_DBS.items():
            db_types.append((info["display"], db_type))

        db_types.sort()  # Sort by display name

        db_type_var = tk.StringVar()
        db_type_combo = ttk.Combobox(
            main_frame, textvariable=db_type_var, state="readonly"
        )
        db_type_combo["values"] = [display for display, _ in db_types]
        db_type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        db_type_combo.current(0)  # Set first option as default

        # Connection parameters frame (will be populated based on selected type)
        params_frame = ttk.LabelFrame(main_frame, text="Connection Parameters")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=10)

        # Dictionary to store parameter entries
        param_entries = {}

        def update_params_frame(*args):
            # Clear existing widgets
            for widget in params_frame.winfo_children():
                widget.destroy()

            # Get selected database type
            selected_display = db_type_var.get()
            selected_type = next((db_type for display, db_type in db_types
                                if display == selected_display), None)

            if not selected_type:
                return

            # Check if required module is installed
            if not ExternalDBConnector.check_dependencies(selected_type):
                module_name = ExternalDBConnector.SUPPORTED_DBS[selected_type]["module"]

                # Show missing dependency message
                ttk.Label(
                    params_frame,
                    text=f"Required module '{module_name}' is not installed.",
                    foreground="red"
                ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

                def install_dependency():
                    btn["state"] = "disabled"
                    status_label["text"] = "Installing module..."

                    def install_task():
                        success = ExternalDBConnector.install_module(module_name)
                        if success:
                            status_label["text"] = f"Successfully installed {module_name}"
                            status_label["foreground"] = "green"
                            # Update the form after installation
                            update_params_frame()
                        else:
                            status_label["text"] = f"Failed to install {module_name}"
                            btn["state"] = "normal"

                    # Run installation in a separate thread
                    threading.Thread(target=install_task).start()

                btn = ttk.Button(
                    params_frame,
                    text=f"Install {module_name}",
                    command=install_dependency
                )
                btn.grid(row=1, column=0, sticky=tk.W, pady=5)

                status_label = ttk.Label(params_frame, text="")
                status_label.grid(row=1, column=1, sticky=tk.W, pady=5)

                return

            # Set up form fields based on database type
            row = 0
            param_entries.clear()

            if selected_type == "mysql":
                fields = [
                    ("Host", "host", "localhost"),
                    ("Port", "port", "3306"),
                    ("User", "user", "root"),
                    ("Password", "password", ""),
                    ("Database", "database", "")
                ]

            elif selected_type == "postgresql":
                fields = [
                    ("Host", "host", "localhost"),
                    ("Port", "port", "5432"),
                    ("User", "user", "postgres"),
                    ("Password", "password", ""),
                    ("Database", "database", "")
                ]

            elif selected_type == "mssql":
                fields = [
                    ("Host", "host", "localhost"),
                    ("Port", "port", "1433"),
                    ("User", "user", "sa"),
                    ("Password", "password", ""),
                    ("Database", "database", "")
                ]

            elif selected_type == "oracle":
                fields = [
                    ("Host", "host", "localhost"),
                    ("Port", "port", "1521"),
                    ("Service Name", "service_name", ""),
                    ("User", "user", ""),
                    ("Password", "password", "")
                ]

            elif selected_type == "sqlite_remote":
                fields = [
                    ("URL", "url", "https://example.com/database.db")
                ]

            elif selected_type in ["csv_file", "json_file", "excel_file"]:
                # Show options for both local file and URL
                ttk.Label(params_frame, text="Choose source:").grid(
                    row=row, column=0, columnspan=2, sticky=tk.W, pady=5
                )
                row += 1

                source_type_var = tk.StringVar(value="local")
                ttk.Radiobutton(
                    params_frame, text="Local File",
                    variable=source_type_var, value="local"
                ).grid(row=row, column=0, sticky=tk.W)

                ttk.Radiobutton(
                    params_frame, text="Remote URL",
                    variable=source_type_var, value="remote"
                ).grid(row=row, column=1, sticky=tk.W)
                row += 1

                # Local file selector
                ttk.Label(params_frame, text="File Path:").grid(
                    row=row, column=0, sticky=tk.W, pady=5
                )

                path_entry = ttk.Entry(params_frame, width=30)
                path_entry.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5)
                param_entries["path"] = path_entry

                def browse_file():
                    file_types = {
                        "csv_file": [("CSV Files", "*.csv")],
                        "json_file": [("JSON Files", "*.json")],
                        "excel_file": [("Excel Files", "*.xlsx;*.xls")]
                    }

                    file_path = filedialog.askopenfilename(
                        title=f"Select {selected_type.split('_')[0].upper()} File",
                        filetypes=file_types[selected_type]
                    )

                    if file_path:
                        path_entry.delete(0, tk.END)
                        path_entry.insert(0, file_path)

                browse_btn = ttk.Button(
                    params_frame, text="Browse...", command=browse_file
                )
                browse_btn.grid(row=row, column=2, sticky=tk.W, pady=5)
                row += 1

                # URL field
                ttk.Label(params_frame, text="URL:").grid(
                    row=row, column=0, sticky=tk.W, pady=5
                )

                url_entry = ttk.Entry(params_frame, width=30)
                url_entry.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5)
                param_entries["url"] = url_entry
                row += 1

                # Toggle fields based on source type
                def toggle_source_fields(*args):
                    if source_type_var.get() == "local":
                        path_entry.config(state="normal")
                        browse_btn.config(state="normal")
                        url_entry.config(state="disabled")
                    else:
                        path_entry.config(state="disabled")
                        browse_btn.config(state="disabled")
                        url_entry.config(state="normal")

                source_type_var.trace_add("write", toggle_source_fields)
                toggle_source_fields()  # Initial setup

                # No more fields needed
                fields = []

            # Create form fields
            for label_text, param_name, default_value in fields:
                ttk.Label(params_frame, text=f"{label_text}:").grid(
                    row=row, column=0, sticky=tk.W, pady=5
                )

                # Use PasswordEntry for password fields
                if param_name == "password":
                    entry = ttk.Entry(params_frame, width=30, show="*")
                else:
                    entry = ttk.Entry(params_frame, width=30)

                entry.insert(0, default_value)
                entry.grid(row=row, column=1, sticky=tk.W+tk.E, pady=5)
                param_entries[param_name] = entry
                row += 1

        # Update form when database type changes
        db_type_combo.bind("<<ComboboxSelected>>", update_params_frame)

        # Initial form setup
        update_params_frame()

        # Test connection button
        def test_connection():
            # Get selected database type
            selected_display = db_type_var.get()
            selected_type = next((db_type for display, db_type in db_types
                                if display == selected_display), None)

            if not selected_type:
                return

            # Collect parameters
            params = {
                key: entry.get() for key, entry in param_entries.items()
                if entry.get()
            }

            # Set status message
            status_var.set("Testing connection...")

            # Run connection test in a thread to avoid freezing UI
            def test_task():
                conn, message = ExternalDBConnector.connect(selected_type, params)

                if conn:
                    # Connection successful
                    status_var.set(f"✓ {message}")
                    # Close connection
                    try:
                        conn.close()
                    except:
                        pass
                else:
                    # Connection failed
                    status_var.set(f"✗ {message}")

            threading.Thread(target=test_task).start()

        # Status message
        status_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=status_var).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=10)

        ttk.Button(
            btn_frame, text="Test Connection", command=test_connection
        ).pack(side=tk.LEFT, padx=5)

        def connect_and_save():
            # Get selected database type
            selected_display = db_type_var.get()
            selected_type = next((db_type for display, db_type in db_types
                                if display == selected_display), None)

            if not selected_type:
                return

            # Collect parameters
            params = {
                key: entry.get() for key, entry in param_entries.items()
                if entry.get()
            }

            # Update status and disable buttons
            status_var.set("Connecting...")
            for child in btn_frame.winfo_children():
                child["state"] = "disabled"

            # Connect in a separate thread
            def connect_task():
                conn, message = ExternalDBConnector.connect(selected_type, params)

                if conn:
                    # Connection successful

                    # For external database types that get converted to SQLite
                    # the connection object will be a SQLite connection
                    # and the message will contain the path to the new database

                    if selected_type in ["sqlite_remote", "csv_file", "json_file", "excel_file"]:
                        # Extract the file path from the message
                        pattern = r"(?:downloaded to|imported to SQLite database:) (.+)"
                        match = re.search(pattern, message)
                        if match:
                            db_path = match.group(1)

                            # Close connection
                            conn.close()

                            # Open the database in the main application
                            if hasattr(self.main_app, 'set_current_database'):
                                self.main_app.set_current_database(db_path)

                            # Refresh the database list and close dialog
                            self.refresh_db_list()
                            dialog.destroy()
                        else:
                            status_var.set("Error: Couldn't determine database path")

                    else:
                        # For other database types, save the connection info
                        conn_info = {
                            "type": selected_type,
                            "display_name": selected_display,
                            "params": params
                        }

                        # Create a name for this connection
                        if "database" in params:
                            name = params["database"]
                        elif "service_name" in params:
                            name = params["service_name"]
                        else:
                            name = f"{selected_type}_db"

                        host = params.get("host", "remote")
                        conn_name = f"{name}@{host}"

                        # Load existing external connections from config
                        config = load_config()
                        external_connections = config.get("external_connections", {})

                        # Add this connection
                        external_connections[conn_name] = conn_info
                        config["external_connections"] = external_connections
                        save_config(config)

                        # Close connection
                        conn.close()

                        # Show success message
                        status_var.set(f"✓ Connection saved as '{conn_name}'")

                        # Re-enable buttons
                        for child in btn_frame.winfo_children():
                            child["state"] = "normal"

                        # Refresh the database list to show the new connection
                        self.refresh_db_list()

                        # Close dialog after a short delay
                        dialog.after(1500, dialog.destroy)

                else:
                    # Connection failed
                    status_var.set(f"✗ {message}")

                    # Re-enable buttons
                    for child in btn_frame.winfo_children():
                        child["state"] = "normal"

            threading.Thread(target=connect_task).start()

        ttk.Button(
            btn_frame, text="Connect & Save", command=connect_and_save
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame, text="Cancel", command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

class ExternalDBConnector:
    """Class to manage connections to external database systems"""

    # Define supported database types and their required modules
    SUPPORTED_DBS = {
        "mysql": {"module": "pymysql", "display": "MySQL"},
        "postgresql": {"module": "psycopg2", "display": "PostgreSQL"},
        "mssql": {"module": "pyodbc", "display": "MS SQL Server"},
        "oracle": {"module": "cx_Oracle", "display": "Oracle"},
        "sqlite_remote": {"module": None, "display": "SQLite (Remote)"},
        "csv_file": {"module": None, "display": "CSV File"},
        "json_file": {"module": None, "display": "JSON File"},
        "excel_file": {"module": "openpyxl", "display": "Excel File"},
    }

    @staticmethod
    def check_dependencies(db_type):
        """Check if the required module for a database type is installed"""
        required_module = ExternalDBConnector.SUPPORTED_DBS.get(db_type, {}).get("module")

        if not required_module:
            return True  # No additional module required

        try:
            importlib.import_module(required_module)
            return True
        except ImportError:
            return False

    @staticmethod
    def install_module(module_name):
        """Install a required module using pip"""
        try:
            import subprocess
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", module_name]
            )
            return True
        except Exception:
            return False

    @staticmethod
    def connect(db_type, params):
        """Connect to an external database based on type and parameters"""
        try:
            if db_type == "mysql":
                import pymysql
                conn = pymysql.connect(
                    host=params.get("host", "localhost"),
                    port=int(params.get("port", 3306)),
                    user=params.get("user", ""),
                    password=params.get("password", ""),
                    database=params.get("database", ""),
                )
                return conn, "MySQL connection successful"

            elif db_type == "postgresql":
                import psycopg2
                conn = psycopg2.connect(
                    host=params.get("host", "localhost"),
                    port=params.get("port", 5432),
                    user=params.get("user", ""),
                    password=params.get("password", ""),
                    dbname=params.get("database", ""),
                )
                return conn, "PostgreSQL connection successful"

            elif db_type == "mssql":
                import pyodbc
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={params.get('host', 'localhost')},"
                    f"{params.get('port', 1433)};"
                    f"DATABASE={params.get('database', '')};"
                    f"UID={params.get('user', '')};"
                    f"PWD={params.get('password', '')}"
                )
                conn = pyodbc.connect(conn_str)
                return conn, "MS SQL Server connection successful"

            elif db_type == "oracle":
                import cx_Oracle
                dsn = cx_Oracle.makedsn(
                    params.get("host", "localhost"),
                    params.get("port", 1521),
                    service_name=params.get("service_name", "")
                )
                conn = cx_Oracle.connect(
                    user=params.get("user", ""),
                    password=params.get("password", ""),
                    dsn=dsn
                )
                return conn, "Oracle connection successful"

            elif db_type == "sqlite_remote":
                # Download the remote SQLite file and create a local connection
                remote_url = params.get("url", "")
                if not remote_url:
                    return None, "No URL provided for remote SQLite database"

                # Generate a local filename
                local_filename = os.path.join(
                    DB_STORAGE_DIR,
                    f"remote_{os.path.basename(remote_url)}"
                )

                # Download the file
                urllib.request.urlretrieve(remote_url, local_filename)

                # Connect to the downloaded file
                conn = sqlite3.connect(local_filename)
                return conn, f"Remote SQLite database downloaded to {local_filename}"

            elif db_type == "csv_file" or db_type == "json_file" or db_type == "excel_file":
                # For these file types, we'll convert them to SQLite
                file_url = params.get("url", "")
                file_path = params.get("path", "")

                if not file_url and not file_path:
                    return None, f"No path or URL provided for {db_type}"

                # Use the URL if provided, otherwise use the local path
                source_path = file_path
                if file_url:
                    # Download the file
                    temp_filename = os.path.join(
                        DB_STORAGE_DIR,
                        f"temp_{os.path.basename(file_url)}"
                    )
                    urllib.request.urlretrieve(file_url, temp_filename)
                    source_path = temp_filename

                # Convert to SQLite
                db_path = os.path.join(
                    DB_STORAGE_DIR,
                    f"{os.path.splitext(os.path.basename(source_path))[0]}.db"
                )

                # Import data based on file type
                if db_type == "csv_file":
                    ExternalDBConnector.import_csv_to_sqlite(source_path, db_path)
                elif db_type == "json_file":
                    ExternalDBConnector.import_json_to_sqlite(source_path, db_path)
                elif db_type == "excel_file":
                    ExternalDBConnector.import_excel_to_sqlite(source_path, db_path)

                # Connect to the new SQLite database
                conn = sqlite3.connect(db_path)
                return conn, f"{db_type} imported to SQLite database: {db_path}"

            else:
                return None, f"Unsupported database type: {db_type}"

        except Exception as e:
            return None, f"Connection error: {str(e)}"

    @staticmethod
    def import_csv_to_sqlite(csv_path, db_path):
        """Import a CSV file into a SQLite database"""
        import csv

        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Get column names from first row

            # Create table
            table_name = os.path.splitext(os.path.basename(csv_path))[0]

            # Clean column names - replace spaces and special chars with underscores
            clean_headers = [re.sub(r'\W+', '_', header).lower() for header in headers]

            # Create the table
            create_stmt = f"CREATE TABLE {table_name} ("
            create_stmt += ", ".join([f"{header} TEXT" for header in clean_headers])
            create_stmt += ")"

            cursor.execute(create_stmt)

            # Insert data
            for row in reader:
                if len(row) == len(headers):
                    placeholders = ", ".join(["?"] * len(row))
                    cursor.execute(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        row
                    )

        # Commit and close
        conn.commit()
        conn.close()

    @staticmethod
    def import_json_to_sqlite(json_path, db_path):
        """Import a JSON file into a SQLite database"""
        import json

        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        table_name = os.path.splitext(os.path.basename(json_path))[0]

        # Handle different JSON structures
        if isinstance(data, list) and len(data) > 0:
            # List of objects - each object becomes a row
            if isinstance(data[0], dict):
                # Get all unique keys from all objects
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())

                # Clean column names
                columns = [re.sub(r'\W+', '_', key).lower() for key in all_keys]

                # Create table
                create_stmt = f"CREATE TABLE {table_name} ("
                create_stmt += ", ".join([f"{col} TEXT" for col in columns])
                create_stmt += ")"

                cursor.execute(create_stmt)

                # Insert data
                for item in data:
                    values = [str(item.get(key, "")) for key in all_keys]
                    placeholders = ", ".join(["?"] * len(values))
                    cursor.execute(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        values
                    )

        elif isinstance(data, dict):
            # Single object or nested structure
            # Create a table for the top level
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    # Create table for this list of objects
                    ExternalDBConnector.create_table_from_json_list(
                        cursor, key, value
                    )

        # Commit and close
        conn.commit()
        conn.close()

    @staticmethod
    def create_table_from_json_list(cursor, table_name, data_list):
        """Helper method to create a table from a list of JSON objects"""
        # Get all unique keys
        all_keys = set()
        for item in data_list:
            all_keys.update(item.keys())

        # Clean column names
        columns = [re.sub(r'\W+', '_', key).lower() for key in all_keys]

        # Create table
        create_stmt = f"CREATE TABLE {table_name} ("
        create_stmt += ", ".join([f"{col} TEXT" for col in columns])
        create_stmt += ")"

        cursor.execute(create_stmt)

        # Insert data
        for item in data_list:
            values = [str(item.get(key, "")) for key in all_keys]
            placeholders = ", ".join(["?"] * len(values))
            cursor.execute(
                f"INSERT INTO {table_name} VALUES ({placeholders})",
                values
            )

    @staticmethod
    def import_excel_to_sqlite(excel_path, db_path):
        """Import an Excel file into a SQLite database"""
        import openpyxl

        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Load Excel file
        workbook = openpyxl.load_workbook(excel_path, read_only=True)

        # Process each sheet
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]

            # Get headers from first row
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value if cell.value else f"col_{len(headers)}")

            # Clean column names
            clean_headers = [re.sub(r'\W+', '_', str(header)).lower() for header in headers]

            # Create table for this sheet
            table_name = re.sub(r'\W+', '_', sheet_name)
            create_stmt = f"CREATE TABLE {table_name} ("
            create_stmt += ", ".join([f"{header} TEXT" for header in clean_headers])
            create_stmt += ")"

            cursor.execute(create_stmt)

            # Insert data from remaining rows
            rows = list(sheet.rows)
            for row in rows[1:]:  # Skip header row
                values = [cell.value if cell.value is not None else "" for cell in row]
                if len(values) == len(headers):
                    placeholders = ", ".join(["?"] * len(values))
                    cursor.execute(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        values
                    )

        # Commit and close
        conn.commit()
        conn.close()

def create_databases_tab(notebook, main_app):
    """
    Create the databases management tab for the notebook.

    Args:
        notebook: The parent notebook widget
        main_app: The main application instance

    Returns:
        The created tab frame
    """
    # Create tab using the DatabaseManagementTab class
    db_tab = DatabaseManagementTab(notebook, main_app)

    # Add the tab to the notebook
    notebook.add(db_tab.tab, text="Databases")

    return db_tab.tab
