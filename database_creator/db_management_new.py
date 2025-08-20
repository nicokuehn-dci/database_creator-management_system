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

from .config import DB_STORAGE_DIR, ensure_directory_exists
from .db_connections import DatabaseConnection
from .db_utils import DatabaseUtils
from .db_table_manager import DatabaseTableManager
from .db_import_export import DatabaseImportExport


class DatabaseManagementTab:
    """Database management tab for the main application"""
    
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
        
        # Initialize tracking variables
        self.db_files = []
        self.current_db = None
        self.current_table = None
        self.current_columns = []
        self.external_conn = None
        self.external_db_type = None
        self.external_conn_string = None
        
        # Ensure database storage directory exists
        ensure_directory_exists(DB_STORAGE_DIR)
        
        # Create the main layout
        self.create_layout()
        
        # Refresh the database list
        self.refresh_db_list()
        
    def create_layout(self):
        """Create the layout for the database management tab"""
        # Create a horizontal paned window
        self.paned = ttk.PanedWindow(self.tab, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Database list
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=1)
        
        # Right side - Database details
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=2)
        
        # Create database list UI
        self._create_database_list_ui()
        
        # Create database info UI
        self._create_database_info_ui()
        
        # Create database data UI
        self._create_database_data_ui()
    
    def _create_database_list_ui(self):
        """Create the UI components for the database list"""
        # Database files list frame
        list_frame = ttk.LabelFrame(self.left_frame, text="Databases")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search and filter controls
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_database_list)
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Sort options
        ttk.Label(filter_frame, text="Sort by:").pack(side=tk.LEFT, padx=(10, 0))
        self.sort_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.sort_var,
            values=["name", "date", "size"],
            state="readonly", 
            width=8
        )
        sort_combo.pack(side=tk.LEFT, padx=5)
        sort_combo.bind("<<ComboboxSelected>>", self.sort_database_list)
        
        # Database listbox with scrollbar
        list_frame_inner = ttk.Frame(list_frame)
        list_frame_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame_inner, orient=tk.VERTICAL)
        self.db_listbox = tk.Listbox(
            list_frame_inner, 
            selectmode=tk.SINGLE,
            exportselection=False,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.db_listbox.yview)
        
        self.db_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.db_listbox.bind("<<ListboxSelect>>", self.on_db_select)
        
        # Button frame for database actions
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons
        refresh_btn = ttk.Button(
            button_frame, text="↻", width=3, command=self.refresh_db_list
        )
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        new_btn = ttk.Button(
            button_frame, text="New", width=8, command=self.create_new_database
        )
        new_btn.pack(side=tk.LEFT, padx=2)
        
        open_btn = ttk.Button(
            button_frame, text="Open", width=8, command=self.open_database_dialog
        )
        open_btn.pack(side=tk.LEFT, padx=2)
        
        connect_btn = ttk.Button(
            button_frame, text="Connect", width=8, command=self.connect_external_database
        )
        connect_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = ttk.Button(
            button_frame, text="Delete", width=8, command=self.delete_selected_database
        )
        delete_btn.pack(side=tk.LEFT, padx=2)
    
    def _create_database_info_ui(self):
        """Create the UI components for the database info"""
        # Info frame
        self.info_frame = ttk.LabelFrame(self.right_frame, text="Database Information")
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid for the info fields
        info_grid = ttk.Frame(self.info_frame)
        info_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Add info labels
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky="w", pady=2)
        self.name_var = tk.StringVar()
        ttk.Label(
            info_grid, textvariable=self.name_var
        ).grid(row=0, column=1, sticky="w", pady=2)
        
        ttk.Label(info_grid, text="Size:").grid(row=1, column=0, sticky="w", pady=2)
        self.size_var = tk.StringVar()
        ttk.Label(
            info_grid, textvariable=self.size_var
        ).grid(row=1, column=1, sticky="w", pady=2)
        
        ttk.Label(info_grid, text="Created:").grid(row=2, column=0, sticky="w", pady=2)
        self.created_var = tk.StringVar()
        ttk.Label(
            info_grid, textvariable=self.created_var
        ).grid(row=2, column=1, sticky="w", pady=2)
        
        ttk.Label(info_grid, text="Modified:").grid(row=3, column=0, sticky="w", pady=2)
        self.modified_var = tk.StringVar()
        ttk.Label(
            info_grid, textvariable=self.modified_var
        ).grid(row=3, column=1, sticky="w", pady=2)
        
        ttk.Label(info_grid, text="Tables:").grid(row=4, column=0, sticky="w", pady=2)
        self.tables_var = tk.StringVar()
        ttk.Label(
            info_grid, textvariable=self.tables_var
        ).grid(row=4, column=1, sticky="w", pady=2)
        
        ttk.Label(info_grid, text="Records:").grid(row=5, column=0, sticky="w", pady=2)
        self.records_var = tk.StringVar()
        ttk.Label(
            info_grid, textvariable=self.records_var
        ).grid(row=5, column=1, sticky="w", pady=2)
        
        # Set column weights
        info_grid.columnconfigure(1, weight=1)
        
        # Tables frame
        tables_frame = ttk.LabelFrame(self.right_frame, text="Tables")
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a listbox for tables
        list_frame = ttk.Frame(tables_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.tables_listbox = tk.Listbox(
            list_frame, 
            selectmode=tk.SINGLE,
            exportselection=False,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tables_listbox.yview)
        
        self.tables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.tables_listbox.bind("<<ListboxSelect>>", self.on_table_selected)
    
    def _create_database_data_ui(self):
        """Create the UI components for the database data"""
        # Data preview frame
        preview_frame = ttk.LabelFrame(self.right_frame, text="Data Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a treeview for data display
        tree_frame = ttk.Frame(preview_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.treeview = ttk.Treeview(
            tree_frame,
            columns=(),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        
        # Configure scrollbars
        y_scroll.config(command=self.treeview.yview)
        x_scroll.config(command=self.treeview.xview)
        
        # Layout
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Info label
        self.data_info_var = tk.StringVar()
        info_label = ttk.Label(preview_frame, textvariable=self.data_info_var)
        info_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Data controls frame
        controls_frame = ttk.Frame(preview_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add row button
        self.add_btn = ttk.Button(
            controls_frame,
            text="Add Row",
            command=self.add_new_row,
            state=tk.DISABLED
        )
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        # Edit row button
        self.edit_btn = ttk.Button(
            controls_frame,
            text="Edit Row",
            command=self.edit_selected_row,
            state=tk.DISABLED
        )
        self.edit_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete row button
        self.delete_btn = ttk.Button(
            controls_frame,
            text="Delete Row",
            command=self.delete_selected_row,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            controls_frame,
            text="↻",
            width=3,
            command=self.refresh_table_data,
            state=tk.DISABLED
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Export button
        self.export_btn = ttk.Button(
            controls_frame,
            text="Export",
            command=self.export_table_data,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.RIGHT, padx=2)
    
    def refresh_db_list(self):
        """Refresh the list of databases"""
        self.db_listbox.delete(0, tk.END)
        self.db_files = []
        
        # List all .db files in the directory
        if os.path.exists(DB_STORAGE_DIR):
            self.db_files = [
                f for f in os.listdir(DB_STORAGE_DIR) 
                if f.endswith('.db') and os.path.isfile(os.path.join(DB_STORAGE_DIR, f))
            ]
        
        # Add external database connections from config
        external_connections = DatabaseConnection.get_external_connections()
        
        # Add them to the list with a special prefix
        for conn_name in external_connections:
            db_type = external_connections[conn_name].get("type", "unknown")
            self.db_files.append(f"[{db_type.upper()}] {conn_name}")
            
        # Apply any filtering and sorting
        self.apply_filters_and_sorting()
        
        # Clear info displays
        self.clear_db_info()
    
    def filter_database_list(self, *_args):
        """Filter the database list based on search text"""
        self.apply_filters_and_sorting()
    
    def sort_database_list(self, *_args):
        """Sort the database list based on selected sort option"""
        self.apply_filters_and_sorting()
    
    def apply_filters_and_sorting(self):
        """Apply filtering and sorting to the database list"""
        # Make a copy of the original list
        filtered_files = self.db_files.copy()
        
        # Apply search filter
        search_text = self.search_var.get().lower()
        if search_text:
            filtered_files = [
                f for f in filtered_files
                if search_text in f.lower()
            ]
        
        # Apply sorting
        sort_option = self.sort_var.get()
        if sort_option == "name":
            # Sort by name, with external connections at the top
            external = [f for f in filtered_files if f.startswith("[")]
            sqlite = [f for f in filtered_files if not f.startswith("[")]
            
            external.sort()
            sqlite.sort()
            filtered_files = external + sqlite
            
        elif sort_option == "date":
            # Sort by modification date (newest first)
            # Only works for SQLite files, external connections are listed first
            external = [f for f in filtered_files if f.startswith("[")]
            sqlite = [f for f in filtered_files if not f.startswith("[")]
            
            external.sort()
            try:
                sqlite.sort(
                    key=lambda f: os.path.getmtime(os.path.join(DB_STORAGE_DIR, f)),
                    reverse=True
                )
            except Exception:
                # Fall back to name sorting if any errors
                sqlite.sort()
                
            filtered_files = external + sqlite
            
        elif sort_option == "size":
            # Sort by file size (largest first)
            # Only works for SQLite files, external connections are listed first
            external = [f for f in filtered_files if f.startswith("[")]
            sqlite = [f for f in filtered_files if not f.startswith("[")]
            
            external.sort()
            try:
                sqlite.sort(
                    key=lambda f: os.path.getsize(os.path.join(DB_STORAGE_DIR, f)),
                    reverse=True
                )
            except Exception:
                # Fall back to name sorting if any errors
                sqlite.sort()
                
            filtered_files = external + sqlite
        
        # Update the listbox
        self.db_listbox.delete(0, tk.END)
        for f in filtered_files:
            self.db_listbox.insert(tk.END, f)
    
    def on_db_select(self, _event=None):
        """Handle selection change in the database listbox"""
        selection = self.db_listbox.curselection()
        if not selection:
            return
            
        db_name = self.db_listbox.get(selection[0])
        is_external = db_name.startswith("[")
        
        if is_external:
            # External database connection
            self.show_external_db_info(db_name)
        else:
            # SQLite database
            db_path = os.path.join(DB_STORAGE_DIR, db_name)
            self.show_db_info(db_path)
    
    def show_db_info(self, db_path):
        """Show information about a SQLite database
        
        Args:
            db_path: Path to the database
        """
        # Clear previous info
        self.clear_db_info()
        
        if not os.path.exists(db_path):
            return
            
        # Set database name
        db_name = os.path.basename(db_path)
        self.name_var.set(db_name)
        
        try:
            # Get database stats
            stats = DatabaseUtils.get_db_stats(db_path)
            
            # Update UI with stats
            self.size_var.set(DatabaseUtils.format_file_size(stats['size']))
            self.created_var.set(
                stats['created'].strftime("%Y-%m-%d %H:%M:%S") 
                if stats['created'] else "N/A"
            )
            self.modified_var.set(
                stats['modified'].strftime("%Y-%m-%d %H:%M:%S")
                if stats['modified'] else "N/A"
            )
            self.tables_var.set(str(stats['tables']))
            self.records_var.set(f"{stats['records']:,}")
            
            # Show tables in listbox
            self.update_tables_list(db_path)
            
            # Update status bar
            self.main_app.set_status(f"Selected database: {db_name}")
            
            # Store current database path
            self.current_db = db_path
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get database info: {str(e)}")
            self.clear_db_info()
    
    def show_external_db_info(self, db_name):
        """Show information about an external database
        
        Args:
            db_name: Formatted name of the database (with type prefix)
        """
        # Clear previous info
        self.clear_db_info()
        
        # Set database name
        self.name_var.set(db_name)
        
        # For external databases, we don't have detailed stats
        self.size_var.set("N/A")
        self.created_var.set("N/A")
        self.modified_var.set("N/A")
        self.tables_var.set("N/A")
        self.records_var.set("N/A")
        
        # Extract the connection name from the formatted string
        if "[" in db_name and "]" in db_name:
            conn_name = db_name[db_name.find("]") + 2:]
            
            # Get connection info
            connections = DatabaseConnection.get_external_connections()
            if conn_name in connections:
                conn_info = connections[conn_name]
                db_type = conn_info.get("type", "unknown")
                host = conn_info.get("host", "")
                database = conn_info.get("database", "")
                
                # Add some connection info
                self.size_var.set(f"Type: {db_type.upper()}")
                self.created_var.set(f"Host: {host}")
                self.modified_var.set(f"Database: {database}")
                
                # Store connection info for potential use
                self.external_conn_string = db_name
                self.external_db_type = db_type
                
                # Display message about external DB limitations
                messagebox.showinfo(
                    "External Database",
                    f"You've selected an external {db_type.upper()} database."
                    f" To work with the data, use the SQL Analytics tab."
                )
                
                # Update status bar
                self.main_app.set_status(f"Connected to external database: {conn_name}")
    
    def update_tables_list(self, db_path):
        """Update the tables listbox for a database
        
        Args:
            db_path: Path to the database
        """
        self.tables_listbox.delete(0, tk.END)
        
        # Get tables
        tables = DatabaseUtils.get_tables_from_sqlite_db(db_path)
        
        # Add to listbox
        for table in sorted(tables):
            self.tables_listbox.insert(tk.END, table)
    
    def on_table_selected(self, _event=None):
        """Handle table selection"""
        selection = self.tables_listbox.curselection()
        if not selection:
            return
            
        table_name = self.tables_listbox.get(selection[0])
        
        # Get selected database
        db_selection = self.db_listbox.curselection()
        if not db_selection:
            return
            
        db_name = self.db_listbox.get(db_selection[0])
        if db_name.startswith("["):
            # External database - can't show data preview
            return
            
        # Load table data
        db_path = os.path.join(DB_STORAGE_DIR, db_name)
        self.show_table_data(db_path, table_name)
    
    def show_table_data(self, db_path, table_name, limit=100):
        """Show data from a table in the treeview
        
        Args:
            db_path: Path to the database
            table_name: Name of the table
            limit: Maximum number of rows to show
        """
        # Clear existing data
        self.clear_treeview()
        
        # Store current table info
        self.current_db = db_path
        self.current_table = table_name
        
        # Get data
        columns, data = DatabaseUtils.get_table_data(db_path, table_name, limit)
        self.current_columns = columns
        
        # Update treeview with data
        self.update_treeview(columns, data)
        
        # Update info
        self.data_info_var.set(f"Showing {len(data)} rows from table '{table_name}'")
        
        # Enable buttons
        self._enable_data_buttons()
        
        # Update status bar
        self.main_app.set_status(f"Loaded table: {table_name}")
    
    def update_treeview(self, columns, data):
        """Update the treeview with new data
        
        Args:
            columns: List of column names
            data: List of data rows
        """
        # Configure columns
        self.treeview["columns"] = columns
        
        # Set column headings
        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, width=100, minwidth=50)
        
        # Add data rows
        for row in data:
            self.treeview.insert("", tk.END, values=row)
    
    def clear_treeview(self):
        """Clear the treeview"""
        # Remove existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)
            
        # Reset columns
        self.treeview["columns"] = ()
        
        # Clear current table info
        self.current_db = None
        self.current_table = None
        self.current_columns = []
        
        # Update info
        self.data_info_var.set("")
        
        # Disable buttons
        self._disable_data_buttons()
    
    def clear_db_info(self):
        """Clear all database info fields"""
        self.name_var.set("")
        self.size_var.set("")
        self.created_var.set("")
        self.modified_var.set("")
        self.tables_var.set("")
        self.records_var.set("")
        self.tables_listbox.delete(0, tk.END)
        
        # Clear data view
        self.clear_treeview()
        
        # Reset external connection info
        self.external_conn_string = None
        self.external_db_type = None
    
    def _enable_data_buttons(self):
        """Enable data control buttons"""
        self.add_btn.config(state=tk.NORMAL)
        self.edit_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
    
    def _disable_data_buttons(self):
        """Disable data control buttons"""
        self.add_btn.config(state=tk.DISABLED)
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
    
    def create_new_database(self):
        """Create a new SQLite database"""
        # Ask for database name
        db_name = simpledialog.askstring(
            "Create Database",
            "Enter database name (without .db extension):",
            parent=self.tab
        )
        
        if not db_name:
            return
            
        # Validate name
        if not re.match(r'^[a-zA-Z0-9_-]+$', db_name):
            messagebox.showerror(
                "Invalid Name",
                "Database name can only contain letters, numbers, underscores, and hyphens."
            )
            return
            
        # Add .db extension if not present
        if not db_name.endswith('.db'):
            db_name += '.db'
            
        # Create full path
        db_path = os.path.join(DB_STORAGE_DIR, db_name)
        
        # Check if file already exists
        if os.path.exists(db_path):
            messagebox.showerror(
                "Error",
                f"A database with the name '{db_name}' already exists."
            )
            return
            
        try:
            # Ensure storage directory exists
            ensure_directory_exists(DB_STORAGE_DIR)
            
            # Create new SQLite database
            conn = sqlite3.connect(db_path)
            conn.close()
            
            # Refresh the database list
            self.refresh_db_list()
            
            # Select the new database
            self.select_database(db_name)
            
            # Update status
            self.main_app.set_status(f"Created new database: {db_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create database: {str(e)}")
    
    def open_database_dialog(self):
        """Open an existing database file"""
        # Show file dialog
        file_path = filedialog.askopenfilename(
            title="Open Database",
            filetypes=[
                ("SQLite Database", "*.db *.sqlite *.sqlite3"), 
                ("All Files", "*.*")
            ],
            initialdir=os.path.expanduser("~")  # Start in user's home directory
        )
        
        if not file_path:
            return
            
        # Get the filename
        db_name = os.path.basename(file_path)
        
        # Create destination path
        dest_path = os.path.join(DB_STORAGE_DIR, db_name)
        
        # Check if a file with this name already exists
        if os.path.exists(dest_path):
            overwrite = messagebox.askyesno(
                "File Already Exists",
                f"A database named '{db_name}' already exists in the storage folder. "
                "Do you want to replace it?"
            )
            if not overwrite:
                return
        
        try:
            # Ensure storage directory exists
            ensure_directory_exists(DB_STORAGE_DIR)
            
            # Copy the file to the storage directory
            shutil.copy2(file_path, dest_path)
            
            # Refresh the database list
            self.refresh_db_list()
            
            # Select the new database
            self.select_database(db_name)
            
            # Update status
            self.main_app.set_status(f"Imported database: {db_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import database: {str(e)}")
    
    def connect_external_database(self):
        """Connect to an external database"""
        # Show connection dialog from the db_connections module
        # This would be implemented in a full application
        messagebox.showinfo(
            "External Database Connection",
            "This feature requires additional database libraries.\n\n"
            "Please install the appropriate library for your database type:\n"
            "- MySQL: pip install pymysql\n"
            "- PostgreSQL: pip install psycopg2\n"
            "- SQL Server: pip install pyodbc\n"
            "- Oracle: pip install cx-Oracle"
        )
        
        # After a successful connection, would refresh the list
        # self.refresh_db_list()
    
    def delete_selected_database(self):
        """Delete the currently selected database"""
        # Get selected database
        selection = self.db_listbox.curselection()
        if not selection:
            return
            
        db_name = self.db_listbox.get(selection[0])
        is_external = db_name.startswith("[")
        
        # Confirm deletion
        if is_external:
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to remove the connection '{db_name}'?\n\n"
                "This will only remove the saved connection, not the actual database."
            )
        else:
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete the database '{db_name}'?\n\n"
                "This cannot be undone!"
            )
            
        if not confirm:
            return
            
        try:
            if is_external:
                # Remove external connection from config
                if "[" in db_name and "]" in db_name:
                    conn_name = db_name[db_name.find("]") + 2:]
                    DatabaseConnection.remove_external_connection(conn_name)
                    self.main_app.set_status(f"Removed connection: {conn_name}")
            else:
                # Delete SQLite database file
                db_path = os.path.join(DB_STORAGE_DIR, db_name)
                if os.path.exists(db_path):
                    os.remove(db_path)
                    self.main_app.set_status(f"Deleted database: {db_name}")
            
            # Refresh the database list
            self.refresh_db_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete database: {str(e)}")
    
    def select_database(self, db_name):
        """Select a database in the listbox by name
        
        Args:
            db_name: Name of the database to select
        """
        # Find and select the database in the listbox
        for i in range(self.db_listbox.size()):
            item_text = self.db_listbox.get(i)
            if item_text == db_name:
                self.db_listbox.selection_clear(0, tk.END)
                self.db_listbox.selection_set(i)
                self.db_listbox.see(i)
                
                # Simulate selection event
                self.on_db_select()
                break
    
    def add_new_row(self):
        """Add a new row to the current table"""
        # Check if we have a table selected
        if not self.current_table or not self.current_db:
            return
            
        table_name = self.current_table
        columns = self.current_columns
        
        # Create dialog for entering values
        self._create_edit_dialog(table_name, columns, [""] * len(columns), is_new=True)
    
    def edit_selected_row(self):
        """Edit the selected row in the current table"""
        # Check if we have a table selected
        if not self.current_table or not self.current_db:
            return
            
        # Get selected row
        selection = self.treeview.selection()
        if not selection:
            messagebox.showinfo("Select Row", "Please select a row to edit.")
            return
            
        # Get row values
        values = self.treeview.item(selection[0])["values"]
        table_name = self.current_table
        columns = self.current_columns
        
        # Create dialog for editing values
        self._create_edit_dialog(table_name, columns, values)
    
    def delete_selected_row(self):
        """Delete the selected row from the current table"""
        # Check if we have a table selected
        if not self.current_table or not self.current_db:
            return
            
        # Get selected row
        selection = self.treeview.selection()
        if not selection:
            messagebox.showinfo("Select Row", "Please select a row to delete.")
            return
            
        # Get row values
        values = self.treeview.item(selection[0])["values"]
        table_name = self.current_table
        columns = self.current_columns
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this row from table '{table_name}'?"
        )
        
        if not confirm:
            return
            
        # Delete the row
        success = DatabaseTableManager.delete_row(
            self.current_db, table_name, columns, values
        )
        
        if success:
            # Refresh the table view
            self.refresh_table_data()
            
            # Update status
            self.main_app.set_status(f"Deleted row from table: {table_name}")
    
    def refresh_table_data(self):
        """Refresh the current table data"""
        if self.current_db and self.current_table:
            self.show_table_data(self.current_db, self.current_table)
    
    def export_table_data(self):
        """Export the current table data"""
        # Check if we have a table selected
        if not self.current_table or not self.current_db:
            return
            
        # Ask for export format
        formats = [
            ("CSV File", "*.csv"),
            ("JSON File", "*.json"),
            ("SQL Insert Statements", "*.sql")
        ]
        
        file_path = filedialog.asksaveasfilename(
            title="Export Table Data",
            filetypes=formats,
            defaultextension=".csv"
        )
        
        if not file_path:
            return
            
        # Determine export format from file extension
        if file_path.endswith(".csv"):
            export_format = "csv"
        elif file_path.endswith(".json"):
            export_format = "json"
        elif file_path.endswith(".sql"):
            export_format = "sql"
        else:
            export_format = "csv"  # Default
        
        # Export the data
        success, message = DatabaseImportExport.export_table_data(
            self.current_db, 
            self.current_table,
            export_format, 
            file_path
        )
        
        if success:
            self.main_app.set_status(message)
        else:
            messagebox.showerror("Export Error", message)
    
    def _create_edit_dialog(self, table_name, columns, values, is_new=False):
        """Create dialog for editing or adding a row
        
        Args:
            table_name: Name of the table
            columns: List of column names
            values: List of current values
            is_new: Whether this is a new row (True) or editing existing (False)
        """
        # Create dialog
        dialog = tk.Toplevel(self.tab)
        dialog.title(f"{'Add' if is_new else 'Edit'} Row in {table_name}")
        dialog.geometry("400x400")
        dialog.transient(self.tab)
        dialog.grab_set()
        
        # Create frame with scrollbar
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a canvas with scrollbar for potentially many fields
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add entries for each column
        entries = []
        for i, col in enumerate(columns):
            ttk.Label(scrollable_frame, text=f"{col}:").grid(
                row=i, column=0, sticky="w", pady=5, padx=5
            )
            
            entry = ttk.Entry(scrollable_frame, width=30)
            if values[i] is not None:
                entry.insert(0, values[i])
            entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
            entries.append(entry)
            
        # Set column weights
        scrollable_frame.columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_data():
            """Save the edited data"""
            # Get new values from entries
            new_values = [entry.get() for entry in entries]
            
            success = False
            if is_new:
                # Insert new row
                success = DatabaseTableManager.add_row(
                    self.current_db, table_name, columns, new_values
                )
            else:
                # Update existing row
                success = DatabaseTableManager.update_row(
                    self.current_db, table_name, columns, values, new_values
                )
            
            if success:
                # Refresh the table view
                self.refresh_table_data()
                
                # Update status
                action = "Added" if is_new else "Updated"
                self.main_app.set_status(f"{action} row in table: {table_name}")
                
                # Close dialog
                dialog.destroy()
        
        # Save button
        save_btn = ttk.Button(button_frame, text="Save", command=save_data)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)


def create_databases_tab(notebook, main_app):
    """
    Create the databases management tab for the notebook.
    
    Args:
        notebook: The parent notebook widget
        main_app: The main application instance
        
    Returns:
        The created tab instance
    """
    # Create the databases management tab
    tab_instance = DatabaseManagementTab(notebook, main_app)
    
    # Add the tab to the notebook
    notebook.add(tab_instance.tab, text="Databases")
    
    return tab_instance
