"""
Graphical User Interface for the database creator application.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sqlite3
from typing import Dict, Any, List, Callable, Optional

from .database import DatabaseManager
from .config import load_config, save_config, DB_STORAGE_DIR
from .templates import DatabaseTemplates
from .security import hash_password
from .advanced_templates import get_advanced_ecommerce_template
from .excel_gui import ExcelTableCreator, ExcelDataEditor
from .db_management import create_databases_tab
from .analytics import create_analytics_tab


class GUI:
    """Graphical User Interface for database creator application."""

    def __init__(self, root=None):
        """Initialize GUI interface."""
        self.config = load_config()
        self.db_manager = None
        self.current_db = None  # Store current database path
        self.templates = DatabaseTemplates()
        self.templates.templates["advanced_ecommerce"] = get_advanced_ecommerce_template()
        
        # Initialize root window if not provided
        if root is None:
            self.root = tk.Tk()
        else:
            self.root = root
            
        # Database management tab will be added in create_tabs
            
        self.root.title("Database Creator")
        self.root.geometry("1000x600")
        
        # Set application icon if available
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except Exception:
            pass
            
        # Create menu bar
        self.create_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Database connection frame
        self.create_db_connection_frame()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        # Add database management tab
        create_databases_tab(self.notebook, self)
        self.create_schema_tab()
        self.create_query_tab()
        self.create_data_tab()
        self.create_templates_tab()
        # Add data analytics tab
        create_analytics_tab(self.notebook, self)
        
        # Try to connect to last database
        last_db = self.config.get('last_database')
        if last_db and os.path.exists(last_db):
            self.connect_database(last_db)
    
    def create_menu(self):
        """Create application menu."""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Database", command=self.new_database)
        file_menu.add_command(label="Open Database", command=self.open_database)
        file_menu.add_separator()
        file_menu.add_command(label="Import SQL", command=self.import_sql)
        file_menu.add_command(label="Export SQL", command=self.export_sql)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Create Table", command=self.create_table_dialog)
        edit_menu.add_command(label="Create Table (Excel-like)", 
                             command=self.create_excel_table)
        edit_menu.add_command(label="Delete Table", command=self.delete_table_dialog)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # Templates menu
        templates_menu = tk.Menu(menu_bar, tearoff=0)
        templates_menu.add_command(label="Apply Template", command=self.apply_template_dialog)
        menu_bar.add_cascade(label="Templates", menu=templates_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def create_db_connection_frame(self):
        """Create database connection frame."""
        db_frame = ttk.LabelFrame(self.main_frame, text="Database Connection")
        db_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(db_frame, text="Current Database:").grid(row=0, column=0, padx=5, pady=5)
        
        self.db_path_var = tk.StringVar()
        self.db_path_var.set("Not connected")
        ttk.Label(db_frame, textvariable=self.db_path_var).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W
        )
        
        ttk.Button(db_frame, text="Open", command=self.open_database).grid(
            row=0, column=2, padx=5, pady=5
        )
        ttk.Button(db_frame, text="New", command=self.new_database).grid(
            row=0, column=3, padx=5, pady=5
        )
    
    def create_schema_tab(self):
        """Create schema tab."""
        schema_frame = ttk.Frame(self.notebook)
        self.notebook.add(schema_frame, text="Schema")
        
        # Left side - table list
        left_frame = ttk.Frame(schema_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Tables:").pack(anchor=tk.W)
        
        # Table list with scrollbar
        table_scroll = ttk.Scrollbar(left_frame)
        self.table_list = tk.Listbox(left_frame, width=30, yscrollcommand=table_scroll.set)
        table_scroll.config(command=self.table_list.yview)
        
        self.table_list.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.table_list.bind('<<ListboxSelect>>', self.on_table_select)
        # Add context menu for Excel-like editing
        self.table_list.bind('<Button-3>', self.on_table_list_right_click)
        
        # Table operations buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Create Table", command=self.create_table_dialog).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Excel Table", command=self.create_excel_table).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Delete Table", command=self.delete_table_dialog).pack(
            side=tk.LEFT, padx=2
        )
        
        # Right side - table details
        right_frame = ttk.Frame(schema_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="Table Structure:").pack(anchor=tk.W)
        
        # Table structure with scrollbar
        columns = ("Column", "Type", "PK", "Not Null", "Default", "Unique")
        self.structure_tree = ttk.Treeview(right_frame, columns=columns, show="headings")
        
        # Set column headings
        for col in columns:
            self.structure_tree.heading(col, text=col)
            self.structure_tree.column(col, width=80)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            right_frame, orient=tk.VERTICAL, command=self.structure_tree.yview
        )
        self.structure_tree.configure(yscrollcommand=y_scroll.set)
        
        self.structure_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_query_tab(self):
        """Create query tab."""
        query_frame = ttk.Frame(self.notebook)
        self.notebook.add(query_frame, text="SQL Query")
        
        # SQL query input
        ttk.Label(query_frame, text="SQL Query:").pack(anchor=tk.W, padx=5, pady=5)
        
        # Text area with scrollbar
        query_scroll = ttk.Scrollbar(query_frame)
        self.query_text = tk.Text(
            query_frame, height=10, yscrollcommand=query_scroll.set
        )
        query_scroll.config(command=self.query_text.yview)
        
        self.query_text.pack(fill=tk.X, padx=5, expand=False)
        query_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Execute button
        ttk.Button(
            query_frame, text="Execute Query", command=self.execute_query
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        # Results area
        ttk.Label(query_frame, text="Results:").pack(anchor=tk.W, padx=5, pady=5)
        
        # Results with scrollbars
        results_frame = ttk.Frame(query_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the Treeview widget
        self.results_tree = ttk.Treeview(results_frame)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            results_frame, orient=tk.VERTICAL, command=self.results_tree.yview
        )
        x_scroll = ttk.Scrollbar(
            results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview
        )
        self.results_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Pack everything
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_data_tab(self):
        """Create data tab."""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data")
        
        # Table selection frame
        selection_frame = ttk.Frame(data_frame)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Select Table:").pack(side=tk.LEFT, padx=5)
        
        self.data_table_var = tk.StringVar()
        self.data_table_combo = ttk.Combobox(
            selection_frame, textvariable=self.data_table_var, state="readonly"
        )
        self.data_table_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.data_table_combo.bind("<<ComboboxSelected>>", self.on_data_table_select)
        
        # Refresh and add buttons
        ttk.Button(
            selection_frame, text="Refresh", command=self.refresh_data_view
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            selection_frame, text="Add Row", command=self.add_row_dialog
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            selection_frame, text="Delete Row", command=self.delete_row
        ).pack(side=tk.LEFT, padx=5)
        
        # Data view
        data_view_frame = ttk.Frame(data_frame)
        data_view_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the Treeview widget
        self.data_tree = ttk.Treeview(data_view_frame)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(
            data_view_frame, orient=tk.VERTICAL, command=self.data_tree.yview
        )
        x_scroll = ttk.Scrollbar(
            data_view_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview
        )
        self.data_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Pack everything
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_templates_tab(self):
        """Create templates tab."""
        templates_frame = ttk.Frame(self.notebook)
        self.notebook.add(templates_frame, text="Templates")
        
        # Left panel - template list
        left_frame = ttk.Frame(templates_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Available Templates:").pack(anchor=tk.W)
        
        # Template list with scrollbar
        template_scroll = ttk.Scrollbar(left_frame)
        self.template_list = tk.Listbox(
            left_frame, width=30, yscrollcommand=template_scroll.set
        )
        template_scroll.config(command=self.template_list.yview)
        
        self.template_list.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        template_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind select event
        self.template_list.bind('<<ListboxSelect>>', self.on_template_select)
        
        # Apply template button
        ttk.Button(
            left_frame, text="Apply Template", command=self.apply_selected_template
        ).pack(pady=5)
        
        # Right panel - template details
        right_frame = ttk.Frame(templates_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="Template Details:").pack(anchor=tk.W)
        
        # Details text with scrollbar
        details_scroll = ttk.Scrollbar(right_frame)
        self.template_details = tk.Text(
            right_frame, wrap=tk.WORD, yscrollcommand=details_scroll.set
        )
        details_scroll.config(command=self.template_details.yview)
        
        self.template_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Make the text read-only
        self.template_details.config(state=tk.DISABLED)
        
        # Load template list
        self.refresh_template_list()
    
    def new_database(self):
        """Create a new database with a user-friendly dialog."""
        # Create a dialog for the new database
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Database")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Database name frame
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(name_frame, text="Database Name:").pack(anchor=tk.W)
        db_name = ttk.Entry(name_frame, width=30)
        db_name.pack(fill=tk.X, pady=5)
        
        # Location options frame
        loc_frame = ttk.LabelFrame(dialog, text="Storage Location")
        loc_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        location_var = tk.StringVar(value="default")
        
        # Default location (in databases folder)
        ttk.Radiobutton(
            loc_frame, 
            text=f"Default location ({os.path.basename(DB_STORAGE_DIR)} folder)", 
            variable=location_var,
            value="default"
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Custom location
        ttk.Radiobutton(
            loc_frame, 
            text="Custom location", 
            variable=location_var,
            value="custom"
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Custom path entry
        custom_frame = ttk.Frame(loc_frame)
        custom_frame.pack(fill=tk.X, padx=30, pady=5)
        
        custom_path = ttk.Entry(custom_frame, width=30)
        custom_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_path():
            path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
            )
            if path:
                custom_path.delete(0, tk.END)
                custom_path.insert(0, path)
                location_var.set("custom")
                
        ttk.Button(custom_frame, text="Browse...", command=browse_path).pack(
            side=tk.RIGHT, padx=5
        )
        
        # Recently used databases
        if self.config.get("recent_databases"):
            recent_frame = ttk.LabelFrame(dialog, text="Recently Used")
            recent_frame.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Radiobutton(
                recent_frame, 
                text="Use a recent database:", 
                variable=location_var,
                value="recent"
            ).pack(anchor=tk.W, padx=10, pady=5)
            
            recent_combo = ttk.Combobox(recent_frame, width=30)
            recent_combo.pack(fill=tk.X, padx=30, pady=5)
            
            # Format the paths for display
            recent_dbs = []
            for db_path in self.config.get("recent_databases", []):
                if os.path.isabs(db_path):
                    recent_dbs.append(db_path)
                else:
                    # It's a relative path in DB_STORAGE_DIR
                    full_path = os.path.join(DB_STORAGE_DIR, db_path)
                    recent_dbs.append(f"{db_path} (in database folder)")
                    
            recent_combo["values"] = recent_dbs
            if recent_dbs:
                recent_combo.current(0)
        
        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        def create_db():
            name = db_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a database name")
                return
                
            # Add .db extension if not present
            if not name.lower().endswith('.db'):
                name = name + ".db"
                
            # Get the path based on location choice
            if location_var.get() == "default":
                # Store in the databases folder
                file_path = os.path.join(DB_STORAGE_DIR, name)
            elif location_var.get() == "custom":
                file_path = custom_path.get()
                if not file_path:
                    messagebox.showerror("Error", "Please specify a custom location")
                    return
            elif location_var.get() == "recent":
                selected_recent = recent_combo.get()
                if "(" in selected_recent:
                    # Extract the relative path
                    rel_path = selected_recent.split("(")[0].strip()
                    file_path = os.path.join(DB_STORAGE_DIR, rel_path)
                else:
                    file_path = selected_recent
            
            # Check if file exists
            if os.path.exists(file_path) and location_var.get() != "recent":
                if not messagebox.askyesno(
                    "File Exists", 
                    "This database already exists. Do you want to open it?"
                ):
                    return
            
            dialog.destroy()
            self.connect_database(file_path)
        
        ttk.Button(btn_frame, text="Create", command=create_db).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(
            btn_frame, text="Cancel", command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def open_database(self):
        """Open an existing database."""
        # First, check the database storage directory
        db_files = []
        if os.path.exists(DB_STORAGE_DIR):
            for file in os.listdir(DB_STORAGE_DIR):
                if file.lower().endswith(".db"):
                    db_files.append(file)
        
        if db_files:
            # If we have databases in the storage directory, show a dialog to choose
            dialog = tk.Toplevel(self.root)
            dialog.title("Open Database")
            dialog.geometry("400x350")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Database selection frame
            ttk.Label(dialog, text="Select a Database:").pack(
                anchor=tk.W, padx=20, pady=(20, 5)
            )
            
            # Create a frame for the listbox and scrollbar
            list_frame = ttk.Frame(dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
            
            # Create scrollbar and listbox
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            db_listbox = tk.Listbox(list_frame, width=50, yscrollcommand=scrollbar.set)
            db_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=db_listbox.yview)
            
            # Add databases to the listbox
            for db_file in sorted(db_files):
                db_listbox.insert(tk.END, db_file)
            
            # Select the first item
            if db_listbox.size() > 0:
                db_listbox.selection_set(0)
                db_listbox.activate(0)
            
            # "Browse" option
            ttk.Separator(dialog).pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Label(dialog, text="Or browse for a database file:").pack(
                anchor=tk.W, padx=20, pady=5
            )
            
            def browse_file():
                file_path = filedialog.askopenfilename(
                    filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
                )
                if file_path:
                    dialog.destroy()
                    self.connect_database(file_path)
            
            ttk.Button(dialog, text="Browse...", command=browse_file).pack(
                anchor=tk.W, padx=20, pady=5
            )
            
            # Buttons frame
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
            
            def open_selected():
                selection = db_listbox.curselection()
                if not selection:
                    messagebox.showinfo("Info", "Please select a database file.")
                    return
                
                db_file = db_listbox.get(selection[0])
                file_path = os.path.join(DB_STORAGE_DIR, db_file)
                dialog.destroy()
                self.connect_database(file_path)
            
            ttk.Button(btn_frame, text="Open", command=open_selected).pack(
                side=tk.RIGHT, padx=5
            )
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
                side=tk.RIGHT, padx=5
            )
            
            # Double-click to open
            db_listbox.bind("<Double-1>", lambda e: open_selected())
            
        else:
            # If no databases in storage directory, go straight to file dialog
            file_path = filedialog.askopenfilename(
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
            )
            
            if file_path:
                self.connect_database(file_path)
    
    def connect_database(self, db_path):
        """Connect to a database."""
        try:
            # Close any existing connection
            if self.db_manager:
                self.db_manager.close()
            
            # Create new connection
            self.db_manager = DatabaseManager(db_path)
            self.current_db = db_path
            self.db_path_var.set(db_path)
            
            # Update config
            self.config['last_database'] = db_path
            save_config(self.config)
            
            # Refresh UI
            self.refresh_table_list()
            self.refresh_data_table_combo()
            
            self.status_var.set(f"Connected to {db_path}")
            
        except sqlite3.Error as e:
            self.show_error(f"Database connection error: {str(e)}")
            
    def set_current_database(self, db_path):
        """Set the current database from an absolute path.
        This method is called by the database management tab.
        
        Args:
            db_path: The absolute path to the database file or None to close
        """
        if db_path is None:
            # Just close the current connection if there is one
            if self.db_manager:
                self.db_manager.close()
                self.db_manager = None
                self.current_db = None
                self.db_path_var.set("")
                self.refresh_table_list()
            return
            
        # Connect to the database
        self.connect_database(db_path)
    
    def refresh_table_list(self):
        """Refresh the list of tables."""
        if not self.db_manager:
            return
            
        try:
            # Clear current list
            self.table_list.delete(0, tk.END)
            
            # Get tables and add to list
            tables = self.db_manager.get_tables()
            for table in sorted(tables):
                self.table_list.insert(tk.END, table)
                
        except sqlite3.Error as e:
            self.show_error(f"Error retrieving tables: {str(e)}")
    
    def on_table_select(self, event):
        """Handle table selection in schema tab."""
        if not self.db_manager:
            return
            
        selection = self.table_list.curselection()
        if not selection:
            return
            
        table_name = self.table_list.get(selection[0])
        self.show_table_structure(table_name)
    
    def show_table_structure(self, table_name):
        """Display the structure of a table."""
        if not self.db_manager:
            return
            
        try:
            # Clear current view
            for item in self.structure_tree.get_children():
                self.structure_tree.delete(item)
            
            # Get schema
            schema = self.db_manager.get_table_schema(table_name)
            
            # Parse and display schema
            for col_info in schema:
                # Extract column information
                parts = col_info.strip().split()
                col_name = parts[0] if parts else ""
                col_type = parts[1] if len(parts) > 1 else ""
                
                # Check for constraints
                is_pk = "Yes" if "PRIMARY KEY" in col_info.upper() else "No"
                not_null = "Yes" if "NOT NULL" in col_info.upper() else "No"
                default_val = ""
                if "DEFAULT" in col_info.upper():
                    start_idx = col_info.upper().find("DEFAULT") + 8
                    default_val = col_info[start_idx:].split()[0]
                
                unique = "Yes" if "UNIQUE" in col_info.upper() else "No"
                
                # Add to treeview
                self.structure_tree.insert(
                    "", tk.END, values=(col_name, col_type, is_pk, not_null, default_val, unique)
                )
                
        except sqlite3.Error as e:
            self.show_error(f"Error retrieving table structure: {str(e)}")
    
    def create_table_dialog(self):
        """Show dialog to create a new table."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Table")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Table name frame
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(name_frame, text="Table Name:").pack(side=tk.LEFT, padx=5)
        table_name = ttk.Entry(name_frame, width=30)
        table_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Columns frame
        columns_frame = ttk.LabelFrame(dialog, text="Columns")
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Columns list
        columns = []
        
        # Function to add column
        def add_column():
            col_name = col_name_entry.get().strip()
            col_type = col_type_entry.get().strip()
            
            if not col_name or not col_type:
                messagebox.showerror("Error", "Column name and type are required.")
                return
                
            constraints = []
            if pk_var.get():
                constraints.append("PRIMARY KEY")
            if not_null_var.get():
                constraints.append("NOT NULL")
            if unique_var.get():
                constraints.append("UNIQUE")
            if default_var.get() and default_entry.get().strip():
                constraints.append(f"DEFAULT {default_entry.get().strip()}")
                
            column_def = f"{col_name} {col_type}"
            if constraints:
                column_def += " " + " ".join(constraints)
                
            columns.append(column_def)
            
            # Add to list
            columns_list.insert(tk.END, column_def)
            
            # Clear entries
            col_name_entry.delete(0, tk.END)
            col_type_entry.delete(0, tk.END)
            default_entry.delete(0, tk.END)
            pk_var.set(False)
            not_null_var.set(False)
            unique_var.set(False)
            default_var.set(False)
        
        # Function to remove column
        def remove_column():
            selection = columns_list.curselection()
            if not selection:
                return
                
            index = selection[0]
            columns.pop(index)
            columns_list.delete(index)
        
        # Function to create table
        def create_table():
            table = table_name.get().strip()
            
            if not table:
                messagebox.showerror("Error", "Table name is required.")
                return
                
            if not columns:
                messagebox.showerror("Error", "At least one column is required.")
                return
                
            try:
                self.db_manager.create_table(table, columns)
                self.refresh_table_list()
                self.refresh_data_table_combo()
                dialog.destroy()
                self.status_var.set(f"Table '{table}' created successfully.")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to create table: {str(e)}")
        
        # Column entry frame
        col_entry_frame = ttk.Frame(columns_frame)
        col_entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(col_entry_frame, text="Name:").grid(row=0, column=0, padx=5)
        col_name_entry = ttk.Entry(col_entry_frame, width=20)
        col_name_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(col_entry_frame, text="Type:").grid(row=0, column=2, padx=5)
        col_type_entry = ttk.Entry(col_entry_frame, width=20)
        col_type_entry.grid(row=0, column=3, padx=5)
        
        # Constraints frame
        constraints_frame = ttk.Frame(columns_frame)
        constraints_frame.pack(fill=tk.X, padx=5, pady=5)
        
        pk_var = tk.BooleanVar()
        ttk.Checkbutton(
            constraints_frame, text="Primary Key", variable=pk_var
        ).grid(row=0, column=0, padx=5)
        
        not_null_var = tk.BooleanVar()
        ttk.Checkbutton(
            constraints_frame, text="Not Null", variable=not_null_var
        ).grid(row=0, column=1, padx=5)
        
        unique_var = tk.BooleanVar()
        ttk.Checkbutton(
            constraints_frame, text="Unique", variable=unique_var
        ).grid(row=0, column=2, padx=5)
        
        default_var = tk.BooleanVar()
        ttk.Checkbutton(
            constraints_frame, text="Default:", variable=default_var
        ).grid(row=0, column=3, padx=5)
        
        default_entry = ttk.Entry(constraints_frame, width=15)
        default_entry.grid(row=0, column=4, padx=5)
        
        # Add/Remove buttons
        button_frame = ttk.Frame(columns_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Column", command=add_column).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Remove Column", command=remove_column).pack(
            side=tk.LEFT, padx=5
        )
        
        # Columns list with scrollbar
        list_frame = ttk.Frame(columns_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scroll = ttk.Scrollbar(list_frame)
        columns_list = tk.Listbox(list_frame, yscrollcommand=scroll.set)
        scroll.config(command=columns_list.yview)
        
        columns_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create/Cancel buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Create", command=create_table).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.RIGHT, padx=5
        )
    
    def delete_table_dialog(self):
        """Show dialog to delete a table."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        selection = self.table_list.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a table to delete.")
            return
            
        table_name = self.table_list.get(selection[0])
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete table '{table_name}'?\n"
            "This action cannot be undone!"
        )
        
        if confirm:
            try:
                self.db_manager.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                self.refresh_table_list()
                self.refresh_data_table_combo()
                self.status_var.set(f"Table '{table_name}' deleted.")
            except sqlite3.Error as e:
                self.show_error(f"Error deleting table: {str(e)}")
    
    def execute_query(self):
        """Execute SQL query from query tab."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        query = self.query_text.get("1.0", tk.END).strip()
        if not query:
            return
            
        try:
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Execute query
            results = self.db_manager.execute_query(query)
            
            # Display results if any
            if results and isinstance(results, list) and results:
                # Configure columns
                if isinstance(results[0], dict):
                    # Set up columns
                    columns = list(results[0].keys())
                    self.results_tree["columns"] = columns
                    
                    # Configure headings
                    for col in columns:
                        self.results_tree.heading(col, text=col)
                        # Adjust column width
                        self.results_tree.column(col, width=100)
                    
                    # Add data rows
                    for row in results:
                        values = [row.get(col, "") for col in columns]
                        self.results_tree.insert("", tk.END, values=values)
                    
                    self.status_var.set(f"Query executed. {len(results)} rows returned.")
                else:
                    # Handle other result formats
                    self.status_var.set("Query executed successfully.")
            else:
                self.status_var.set("Query executed successfully. No results.")
                
            # Refresh UI after potential changes
            self.refresh_table_list()
            self.refresh_data_table_combo()
            
        except sqlite3.Error as e:
            self.show_error(f"SQL Error: {str(e)}")
    
    def refresh_data_table_combo(self):
        """Refresh the table combobox in data tab."""
        if not self.db_manager:
            return
            
        try:
            # Get tables
            tables = self.db_manager.get_tables()
            
            # Update combobox
            self.data_table_combo['values'] = sorted(tables)
            
            if tables:
                self.data_table_var.set(tables[0])
                self.on_data_table_select(None)
            else:
                self.data_table_var.set("")
                
        except sqlite3.Error as e:
            self.show_error(f"Error refreshing tables: {str(e)}")
    
    def on_data_table_select(self, event):
        """Handle table selection in data tab."""
        table = self.data_table_var.get()
        if table:
            self.load_table_data(table)
    
    def load_table_data(self, table_name):
        """Load data from table."""
        if not self.db_manager:
            return
            
        try:
            # Clear previous data
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
                
            # Get table data
            results = self.db_manager.execute_query(f"SELECT * FROM {table_name}")
            
            if results and isinstance(results, list) and results:
                # Set up columns
                columns = list(results[0].keys())
                self.data_tree["columns"] = columns
                
                # Configure headings
                for col in columns:
                    self.data_tree.heading(col, text=col)
                    # Adjust column width
                    self.data_tree.column(col, width=100)
                
                # Add data rows
                for row in results:
                    values = [row.get(col, "") for col in columns]
                    self.data_tree.insert("", tk.END, values=values)
                
                self.status_var.set(f"Loaded {len(results)} rows from {table_name}")
            else:
                self.status_var.set(f"Table {table_name} is empty.")
                
        except sqlite3.Error as e:
            self.show_error(f"Error loading table data: {str(e)}")
    
    def refresh_data_view(self):
        """Refresh the data view."""
        table = self.data_table_var.get()
        if table:
            self.load_table_data(table)
    
    def add_row_dialog(self):
        """Show dialog to add a new row."""
        if not self.db_manager:
            return
            
        table = self.data_table_var.get()
        if not table:
            messagebox.showinfo("Info", "Please select a table first.")
            return
            
        try:
            # Get table schema
            schema = self.db_manager.get_table_schema(table)
            
            # Create dialog
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Add Row to {table}")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Field entries
            entries = {}
            row = 0
            
            for col_info in schema:
                # Extract column name and type
                parts = col_info.strip().split()
                col_name = parts[0] if parts else ""
                col_type = parts[1] if len(parts) > 1 else ""
                
                # Skip auto-increment columns
                if "AUTOINCREMENT" in col_info.upper():
                    continue
                
                ttk.Label(dialog, text=f"{col_name} ({col_type}):").grid(
                    row=row, column=0, padx=5, pady=5, sticky=tk.W
                )
                
                entry = ttk.Entry(dialog, width=30)
                entry.grid(row=row, column=1, padx=5, pady=5)
                entries[col_name] = entry
                
                row += 1
            
            # Save function
            def save_row():
                # Get values
                data = {}
                for name, entry in entries.items():
                    value = entry.get().strip()
                    # Only add non-empty values
                    if value:
                        data[name] = value
                
                try:
                    if data:
                        self.db_manager.insert_into_table(table, data)
                        self.load_table_data(table)
                        dialog.destroy()
                        self.status_var.set(f"Row added to {table}")
                    else:
                        messagebox.showinfo("Info", "No data entered.")
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Failed to add row: {str(e)}")
            
            # Buttons
            btn_frame = ttk.Frame(dialog)
            btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
            
            ttk.Button(btn_frame, text="Save", command=save_row).pack(
                side=tk.LEFT, padx=5
            )
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
                side=tk.LEFT, padx=5
            )
            
        except sqlite3.Error as e:
            self.show_error(f"Error getting table structure: {str(e)}")
    
    def delete_row(self):
        """Delete selected row."""
        if not self.db_manager:
            return
            
        table = self.data_table_var.get()
        if not table:
            return
            
        # Get selected row
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a row to delete.")
            return
            
        # Get row data
        item = selection[0]
        values = self.data_tree.item(item, "values")
        
        # Get primary key column if available
        try:
            schema = self.db_manager.get_table_schema(table)
            pk_col = None
            
            for col_info in schema:
                if "PRIMARY KEY" in col_info.upper():
                    pk_col = col_info.strip().split()[0]
                    break
            
            # If primary key found, use it for deletion
            if pk_col:
                # Get column names to find primary key value
                columns = self.data_tree["columns"]
                pk_index = columns.index(pk_col)
                pk_value = values[pk_index]
                
                # Confirm deletion
                confirm = messagebox.askyesno(
                    "Confirm Delete", 
                    f"Are you sure you want to delete this row?"
                )
                
                if confirm:
                    self.db_manager.execute_query(
                        f"DELETE FROM {table} WHERE {pk_col} = ?", 
                        (pk_value,)
                    )
                    self.load_table_data(table)
                    self.status_var.set("Row deleted.")
            else:
                messagebox.showinfo(
                    "Info", 
                    "Cannot delete row: No primary key found in table."
                )
                
        except sqlite3.Error as e:
            self.show_error(f"Error deleting row: {str(e)}")
    
    def refresh_template_list(self):
        """Refresh the template list."""
        # Clear current list
        self.template_list.delete(0, tk.END)
        
        # Add templates
        for template_name in self.templates.templates:
            self.template_list.insert(tk.END, template_name)
    
    def on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_list.curselection()
        if not selection:
            return
            
        template_name = self.template_list.get(selection[0])
        self.show_template_details(template_name)
    
    def show_template_details(self, template_name):
        """Show details of selected template."""
        template = self.templates.templates.get(template_name)
        if not template:
            return
            
        # Enable text editing
        self.template_details.config(state=tk.NORMAL)
        
        # Clear current text
        self.template_details.delete("1.0", tk.END)
        
        # Add template details
        self.template_details.insert(tk.END, f"Template: {template_name}\n\n")
        
        for table_name, table_def in template.items():
            self.template_details.insert(
                tk.END, 
                f"Table: {table_name}\n{'-' * (len(table_name) + 7)}\n"
            )
            
            # Add columns
            self.template_details.insert(tk.END, "Columns:\n")
            for col_name, col_type in table_def.get('columns', {}).items():
                self.template_details.insert(tk.END, f"  {col_name}: {col_type}\n")
            
            # Add constraints if any
            constraints = table_def.get('constraints', [])
            if constraints:
                self.template_details.insert(tk.END, "\nConstraints:\n")
                for constraint in constraints:
                    self.template_details.insert(tk.END, f"  {constraint}\n")
            
            self.template_details.insert(tk.END, "\n")
        
        # Make read-only again
        self.template_details.config(state=tk.DISABLED)
    
    def apply_template_dialog(self):
        """Show dialog to apply a template."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Apply Template")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Template:").grid(
            row=0, column=0, padx=10, pady=10, sticky=tk.W
        )
        
        # Template combobox
        template_var = tk.StringVar()
        template_combo = ttk.Combobox(
            dialog, textvariable=template_var, state="readonly", width=30
        )
        template_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # Fill with template names
        template_combo['values'] = list(self.templates.templates.keys())
        
        # Warning label
        warning_label = ttk.Label(
            dialog, 
            text="Warning: This will create tables in your database.\n"
                 "Existing tables with the same names will not be modified.",
            foreground="red"
        )
        warning_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        # Apply function
        def apply():
            template_name = template_var.get()
            if not template_name:
                messagebox.showinfo("Info", "Please select a template.")
                return
            
            confirm = messagebox.askyesno(
                "Confirm Apply", 
                f"Are you sure you want to apply the '{template_name}' template?"
            )
            
            if confirm:
                try:
                    self.apply_template(template_name)
                    dialog.destroy()
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Failed to apply template: {str(e)}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Apply", command=apply).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )
    
    def apply_selected_template(self):
        """Apply the selected template from templates tab."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        selection = self.template_list.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a template.")
            return
            
        template_name = self.template_list.get(selection[0])
        
        confirm = messagebox.askyesno(
            "Confirm Apply", 
            f"Are you sure you want to apply the '{template_name}' template?"
        )
        
        if confirm:
            try:
                self.apply_template(template_name)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to apply template: {str(e)}")
    
    def apply_template(self, template_name):
        """Apply a template to the database."""
        template = self.templates.templates.get(template_name)
        if not template:
            messagebox.showerror("Error", f"Template '{template_name}' not found.")
            return
        
        try:
            for table_name, table_def in template.items():
                columns = table_def.get('columns', {})
                constraints = table_def.get('constraints', [])
                
                # Format columns for create_table
                column_defs = [f"{name} {dtype}" for name, dtype in columns.items()]
                
                # Add any additional constraints
                if constraints:
                    column_defs.extend(constraints)
                
                # Create the table
                self.db_manager.create_table(table_name, column_defs)
            
            # Refresh UI
            self.refresh_table_list()
            self.refresh_data_table_combo()
            
            self.status_var.set(f"Template '{template_name}' applied successfully.")
        except Exception as e:
            self.show_error(f"Error applying template: {str(e)}")
    
    def import_sql(self):
        """Import database from SQL file."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.db_manager.import_from_sql(file_path)
                self.refresh_table_list()
                self.refresh_data_table_combo()
                self.status_var.set(f"Database imported from {file_path}")
            except Exception as e:
                self.show_error(f"Error importing database: {str(e)}")
    
    def export_sql(self):
        """Export database to SQL file."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.db_manager.export_to_sql(file_path)
                self.status_var.set(f"Database exported to {file_path}")
            except Exception as e:
                self.show_error(f"Error exporting database: {str(e)}")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Database Creator",
            "Database Creator\n"
            "Version 1.0\n\n"
            "A simple SQLite database manager.\n"
            "Create, modify, and manage SQLite databases with ease."
        )
    
    def show_error(self, message):
        """Show error message."""
        messagebox.showerror("Error", message)
        self.status_var.set("Error: See error dialog")
    
    def create_excel_table(self):
        """Show the Excel-like table creator dialog."""
        if not self.db_manager:
            messagebox.showinfo("Info", "Please connect to a database first.")
            return
            
        ExcelTableCreator(
            self.root, 
            self.db_manager,
            on_table_created=lambda: (
                self.refresh_table_list(),
                self.refresh_data_table_combo(),
                self.status_var.set("Table created successfully.")
            )
        )
        
    def on_table_list_right_click(self, event):
        """Handle right click on table list."""
        if not self.db_manager:
            return
            
        # Select the item under cursor
        index = self.table_list.nearest(event.y)
        if index >= 0:
            self.table_list.selection_clear(0, tk.END)
            self.table_list.selection_set(index)
            self.table_list.activate(index)
            table_name = self.table_list.get(index)
            
            # Create popup menu
            popup = tk.Menu(self.root, tearoff=0)
            popup.add_command(label="View Structure", 
                            command=lambda: self.display_table_structure(table_name))
            popup.add_command(label="Edit Data (Excel-like)", 
                            command=lambda: self.edit_table_data_excel(table_name))
            popup.add_separator()
            popup.add_command(label="Delete Table", 
                            command=lambda: self.delete_table_confirm(table_name))
            
            # Display the popup menu
            try:
                popup.tk_popup(event.x_root, event.y_root, 0)
            finally:
                popup.grab_release()
                
    def edit_table_data_excel(self, table_name):
        """Open the Excel-like editor for table data."""
        if not self.db_manager:
            return
            
        ExcelDataEditor(self.root, self.db_manager, table_name)
        
    def delete_table_confirm(self, table_name):
        """Delete a table with confirmation."""
        if not self.db_manager:
            return
            
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete table '{table_name}'?\n"
            "This action cannot be undone!"
        )
        
        if confirm:
            try:
                self.db_manager.execute_query(f"DROP TABLE IF EXISTS {table_name}")
                self.refresh_table_list()
                self.refresh_data_table_combo()
                self.status_var.set(f"Table '{table_name}' deleted successfully.")
            except sqlite3.Error as e:
                self.show_error(f"Failed to delete table: {str(e)}")
        
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Entry point for GUI application."""
    gui = GUI()
    gui.run()


if __name__ == "__main__":
    main()
