"""
UI components for the database management tab.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import datetime
import threading

from .config import DB_STORAGE_DIR, ensure_directory_exists
from .db_connections import DatabaseConnection, DatabaseUtils


class DatabaseListUI:
    """UI components for database listing and filtering"""
    
    def __init__(self, parent, on_select_callback=None, on_refresh_callback=None):
        """
        Initialize the database list UI.
        
        Args:
            parent: Parent frame
            on_select_callback: Function to call when a database is selected
            on_refresh_callback: Function to call when database list is refreshed
        """
        self.parent = parent
        self.on_select_callback = on_select_callback
        self.on_refresh_callback = on_refresh_callback
        
        # Database files list
        self.db_files = []
        
        # Create UI components
        self._create_ui()
        
    def _create_ui(self):
        """Create the UI components"""
        # List frame with label
        list_frame = ttk.LabelFrame(self.parent, text="Databases")
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
        self.db_listbox.bind("<<ListboxSelect>>", self._on_selection_changed)
        
        # Button frame for database actions
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Refresh button
        refresh_btn = ttk.Button(
            button_frame,
            text="↻",
            width=3, 
            command=self.refresh_db_list
        )
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # New button
        new_btn = ttk.Button(
            button_frame,
            text="New",
            width=8, 
            command=self._on_new_clicked
        )
        new_btn.pack(side=tk.LEFT, padx=2)
        
        # Open button
        open_btn = ttk.Button(
            button_frame,
            text="Open",
            width=8, 
            command=self._on_open_clicked
        )
        open_btn.pack(side=tk.LEFT, padx=2)
        
        # Connect button for external databases
        connect_btn = ttk.Button(
            button_frame,
            text="Connect",
            width=8, 
            command=self._on_connect_clicked
        )
        connect_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete button
        delete_btn = ttk.Button(
            button_frame,
            text="Delete",
            width=8, 
            command=self._on_delete_clicked
        )
        delete_btn.pack(side=tk.LEFT, padx=2)
        
    def refresh_db_list(self):
        """Refresh the list of databases"""
        self.db_listbox.delete(0, tk.END)
        
        # Ensure the directory exists
        ensure_directory_exists(DB_STORAGE_DIR)
        
        # List all .db files in the directory
        self.db_files = []
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
        
        # Notify callback if provided
        if self.on_refresh_callback:
            self.on_refresh_callback()
    
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
            sqlite.sort(
                key=lambda f: os.path.getmtime(os.path.join(DB_STORAGE_DIR, f)),
                reverse=True
            )
            filtered_files = external + sqlite
            
        elif sort_option == "size":
            # Sort by file size (largest first)
            # Only works for SQLite files, external connections are listed first
            external = [f for f in filtered_files if f.startswith("[")]
            sqlite = [f for f in filtered_files if not f.startswith("[")]
            
            external.sort()
            sqlite.sort(
                key=lambda f: os.path.getsize(os.path.join(DB_STORAGE_DIR, f)),
                reverse=True
            )
            filtered_files = external + sqlite
        
        # Update the listbox
        self.db_listbox.delete(0, tk.END)
        for f in filtered_files:
            self.db_listbox.insert(tk.END, f)
    
    def get_selected_database(self):
        """Get the currently selected database
        
        Returns:
            Tuple of (db_name, is_external)
        """
        selection = self.db_listbox.curselection()
        if not selection:
            return None, False
            
        db_name = self.db_listbox.get(selection[0])
        is_external = db_name.startswith("[")
        
        return db_name, is_external
        
    def _on_selection_changed(self, _event=None):
        """Handle selection change in the database listbox"""
        if self.on_select_callback:
            db_name, is_external = self.get_selected_database()
            if db_name:
                self.on_select_callback(db_name, is_external)
    
    def _on_new_clicked(self):
        """Handle click on New button"""
        # This should be implemented by the parent class
        pass
    
    def _on_open_clicked(self):
        """Handle click on Open button"""
        # This should be implemented by the parent class
        pass
    
    def _on_connect_clicked(self):
        """Handle click on Connect button"""
        # This should be implemented by the parent class
        pass
    
    def _on_delete_clicked(self):
        """Handle click on Delete button"""
        # This should be implemented by the parent class
        pass


class DatabaseInfoUI:
    """UI components for displaying database information"""
    
    def __init__(self, parent):
        """
        Initialize the database info UI.
        
        Args:
            parent: Parent frame
        """
        self.parent = parent
        
        # Create UI components
        self._create_ui()
        
    def _create_ui(self):
        """Create the UI components"""
        # Create the info frame
        self.info_frame = ttk.LabelFrame(self.parent, text="Database Information")
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
        tables_frame = ttk.LabelFrame(self.parent, text="Tables")
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
    
    def update_info(self, db_name, db_path=None, is_external=False):
        """Update the database information display
        
        Args:
            db_name: Name of the database
            db_path: Path to the database file (for SQLite only)
            is_external: Whether this is an external database
        """
        # Update the name
        self.name_var.set(db_name)
        
        if is_external:
            # For external databases, we don't have detailed stats
            self.size_var.set("N/A")
            self.created_var.set("N/A")
            self.modified_var.set("N/A")
            self.tables_var.set("N/A")
            self.records_var.set("N/A")
            
            # Clear tables list
            self.tables_listbox.delete(0, tk.END)
            
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
                    
                    # TODO: In the future, could query table list from external DB
            
        elif db_path and os.path.exists(db_path):
            # For SQLite databases, show detailed info
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
                self.update_tables(db_path)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to get database info: {str(e)}")
                self.clear_info()
        else:
            self.clear_info()
    
    def update_tables(self, db_path):
        """Update the tables listbox for a SQLite database
        
        Args:
            db_path: Path to the database file
        """
        self.tables_listbox.delete(0, tk.END)
        
        # Get tables
        tables = DatabaseUtils.get_tables_from_sqlite_db(db_path)
        
        # Add to listbox
        for table in sorted(tables):
            self.tables_listbox.insert(tk.END, table)
    
    def clear_info(self):
        """Clear all database info fields"""
        self.name_var.set("")
        self.size_var.set("")
        self.created_var.set("")
        self.modified_var.set("")
        self.tables_var.set("")
        self.records_var.set("")
        self.tables_listbox.delete(0, tk.END)
        
    def get_selected_table(self):
        """Get the currently selected table
        
        Returns:
            Table name or None if no selection
        """
        selection = self.tables_listbox.curselection()
        if not selection:
            return None
            
        return self.tables_listbox.get(selection[0])


class TableDataUI:
    """UI components for displaying table data"""
    
    def __init__(self, parent):
        """
        Initialize the table data UI.
        
        Args:
            parent: Parent frame
        """
        self.parent = parent
        
        # Current table state
        self.current_db = None
        self.current_table = None
        self.current_columns = []
        
        # Create UI components
        self._create_ui()
        
    def _create_ui(self):
        """Create the UI components"""
        # Data preview frame
        preview_frame = ttk.LabelFrame(self.parent, text="Data Preview")
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
        self.info_var = tk.StringVar()
        info_label = ttk.Label(preview_frame, textvariable=self.info_var)
        info_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Data controls frame
        controls_frame = ttk.Frame(preview_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add row button
        self.add_btn = ttk.Button(
            controls_frame,
            text="Add Row",
            command=self._on_add_clicked,
            state=tk.DISABLED
        )
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        # Edit row button
        self.edit_btn = ttk.Button(
            controls_frame,
            text="Edit Row",
            command=self._on_edit_clicked,
            state=tk.DISABLED
        )
        self.edit_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete row button
        self.delete_btn = ttk.Button(
            controls_frame,
            text="Delete Row",
            command=self._on_delete_clicked,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            controls_frame,
            text="↻",
            width=3,
            command=self._on_refresh_clicked,
            state=tk.DISABLED
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Export button
        self.export_btn = ttk.Button(
            controls_frame,
            text="Export",
            command=self._on_export_clicked,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.RIGHT, padx=2)
    
    def load_table_data(self, db_path, table_name, limit=100):
        """Load data from a table into the treeview
        
        Args:
            db_path: Path to the database file
            table_name: Name of the table
            limit: Maximum number of rows to load
        """
        # Store current table info
        self.current_db = db_path
        self.current_table = table_name
        
        # Get data
        columns, data = DatabaseUtils.get_table_data(db_path, table_name, limit)
        self.current_columns = columns
        
        # Update treeview
        self.update_treeview(columns, data)
        
        # Update info
        self.info_var.set(f"Showing {len(data)} rows from table '{table_name}'")
        
        # Enable buttons
        self._enable_buttons()
    
    def update_treeview(self, columns, data):
        """Update the treeview with new data
        
        Args:
            columns: List of column names
            data: List of data rows
        """
        # Clear existing data
        self.clear_treeview()
        
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
        self.info_var.set("")
        
        # Disable buttons
        self._disable_buttons()
    
    def _enable_buttons(self):
        """Enable data control buttons"""
        self.add_btn.config(state=tk.NORMAL)
        self.edit_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
    
    def _disable_buttons(self):
        """Disable data control buttons"""
        self.add_btn.config(state=tk.DISABLED)
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
    
    def _on_add_clicked(self):
        """Handle click on Add Row button"""
        # This should be implemented by the parent class
        pass
    
    def _on_edit_clicked(self):
        """Handle click on Edit Row button"""
        # This should be implemented by the parent class
        pass
    
    def _on_delete_clicked(self):
        """Handle click on Delete Row button"""
        # This should be implemented by the parent class
        pass
    
    def _on_refresh_clicked(self):
        """Handle click on Refresh button"""
        if self.current_db and self.current_table:
            self.load_table_data(self.current_db, self.current_table)
    
    def _on_export_clicked(self):
        """Handle click on Export button"""
        # This should be implemented by the parent class
        pass
