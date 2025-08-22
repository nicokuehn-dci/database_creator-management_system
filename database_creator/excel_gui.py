"""
Excel-like table creation interface for the database creator.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from typing import Dict, List, Any, Optional, Tuple

from .database import DatabaseManager

class ExcelTableCreator:
    """Excel-like interface for creating database tables."""

    def __init__(self, parent, db_manager: DatabaseManager, on_table_created=None):
        """
        Initialize the Excel-like table creator.

        Args:
            parent: Parent tkinter widget
            db_manager: DatabaseManager instance
            on_table_created: Callback function to run after table creation
        """
        self.parent = parent
        self.db_manager = db_manager
        self.on_table_created = on_table_created

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Excel-like Table Creator")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Configure row and column weights
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(2, weight=1)

        # Table name frame
        name_frame = ttk.Frame(self.dialog)
        name_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(name_frame, text="Table Name:").pack(side=tk.LEFT, padx=5)
        self.table_name = ttk.Entry(name_frame, width=30)
        self.table_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Buttons frame
        btn_top_frame = ttk.Frame(self.dialog)
        btn_top_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        ttk.Button(btn_top_frame, text="Add Column", command=self.add_column).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_top_frame, text="Add Row", command=self.add_row).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_top_frame, text="Delete Selected", command=self.delete_selected).pack(
            side=tk.LEFT, padx=5
        )

        # Create table for spreadsheet view
        self.sheet_frame = ttk.Frame(self.dialog)
        self.sheet_frame.grid(row=2, column=0, padx=10, pady=0, sticky="nsew")

        # Create the treeview with vertical scrollbars
        self.sheet = ttk.Treeview(self.sheet_frame)

        vsb = ttk.Scrollbar(self.sheet_frame, orient="vertical", command=self.sheet.yview)
        self.sheet.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(self.sheet_frame, orient="horizontal", command=self.sheet.xview)
        self.sheet.configure(xscrollcommand=hsb.set)

        # Place the scrollbars
        self.sheet.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure weights in sheet_frame
        self.sheet_frame.grid_columnconfigure(0, weight=1)
        self.sheet_frame.grid_rowconfigure(0, weight=1)

        # Column types frame
        self.column_types_frame = ttk.LabelFrame(self.dialog, text="Column Types")
        self.column_types_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # Data preview frame (shows data as SQL-style rows)
        self.preview_frame = ttk.LabelFrame(self.dialog, text="SQL Preview")
        self.preview_frame.grid(row=4, column=0, padx=10, pady=0, sticky="ew")

        self.preview_text = tk.Text(self.preview_frame, height=5, wrap=tk.NONE)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create/Cancel buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        ttk.Button(btn_frame, text="Create Table", command=self.create_table).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(
            side=tk.RIGHT, padx=5
        )

        # Initialize the sheet
        self.col_count = 1  # Start with 1 column (ID)
        self.initialize_sheet()

        # Add initial column (ID with INTEGER PRIMARY KEY)
        self.add_column("ID", "INTEGER PRIMARY KEY")

        # Update the preview when the table is changed
        self.sheet.bind("<<TreeviewSelect>>", self.update_preview)

    def initialize_sheet(self):
        """Initialize the sheet with headers."""
        # Clear current tree
        for item in self.sheet.get_children():
            self.sheet.delete(item)

        # Define columns
        self.sheet["columns"] = []

        # Configure column properties
        self.sheet.column("#0", width=0, stretch=tk.NO)  # Hide first column
        self.sheet.heading("#0", text="")

        # Add column type editors
        for widget in self.column_types_frame.winfo_children():
            widget.destroy()

        # Header row (locked)
        self.sheet.insert("", tk.END, text="", values=[], tags=["header"], iid="header")

    def add_column(self, name: Optional[str] = None, data_type: Optional[str] = None):
        """Add a new column to the sheet."""
        if not name:
            # Default column name
            name = f"Column{self.col_count}"

        if not data_type:
            # Default data type
            data_type = "TEXT"

        # Add column to treeview
        col_id = f"col{self.col_count}"
        cols = list(self.sheet["columns"])
        cols.append(col_id)
        self.sheet["columns"] = cols

        self.sheet.column(col_id, width=100, minwidth=50, anchor=tk.CENTER)
        self.sheet.heading(col_id, text=name)

        # Add column type editor
        col_frame = ttk.Frame(self.column_types_frame)
        col_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

        ttk.Label(col_frame, text=name).pack(anchor=tk.W)

        # Create combo box for data type
        type_var = tk.StringVar(value=data_type)
        type_combo = ttk.Combobox(
            col_frame,
            textvariable=type_var,
            values=["INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC", "DATE", "DATETIME", "BOOLEAN"],
            width=10
        )
        type_combo.pack(pady=2)

        # Add constraints checkboxes
        constraints_frame = ttk.Frame(col_frame)
        constraints_frame.pack(pady=2)

        pk_var = tk.BooleanVar(value="PRIMARY KEY" in data_type)
        not_null_var = tk.BooleanVar(value=False)
        unique_var = tk.BooleanVar(value=False)

        if data_type == "INTEGER PRIMARY KEY":
            pk_var.set(True)

        ttk.Checkbutton(constraints_frame, text="PK", variable=pk_var).grid(row=0, column=0)
        ttk.Checkbutton(constraints_frame, text="NN", variable=not_null_var).grid(row=0, column=1)
        ttk.Checkbutton(constraints_frame, text="UQ", variable=unique_var).grid(row=0, column=2)

        # Store references to all variables
        setattr(self, f"col_{self.col_count}_name", tk.StringVar(value=name))
        setattr(self, f"col_{self.col_count}_type", type_var)
        setattr(self, f"col_{self.col_count}_pk", pk_var)
        setattr(self, f"col_{self.col_count}_nn", not_null_var)
        setattr(self, f"col_{self.col_count}_uq", unique_var)

        # Add data to header row
        header_values = list(self.sheet.item("header", "values"))
        while len(header_values) < self.col_count:
            header_values.append("")
        self.sheet.item("header", values=header_values)

        # Update existing rows with empty value for new column
        for item_id in self.sheet.get_children():
            if item_id != "header":
                values = list(self.sheet.item(item_id, "values"))
                while len(values) < self.col_count:
                    values.append("")
                self.sheet.item(item_id, values=values)

        # Update counter
        self.col_count += 1

        # Update preview
        self.update_preview()

    def add_row(self):
        """Add a new row to the sheet."""
        # Create empty row
        values = [""] * (self.col_count - 1)
        self.sheet.insert("", tk.END, text="", values=values)

        # Update preview
        self.update_preview()

    def delete_selected(self):
        """Delete selected rows or columns."""
        selection = self.sheet.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a row to delete.")
            return

        # Don't allow deleting the header row
        if "header" in selection:
            selection = [item for item in selection if item != "header"]

        # Delete selected rows
        for item in selection:
            self.sheet.delete(item)

        # Update preview
        self.update_preview()

    def update_preview(self, event=None):
        """Update the SQL preview."""
        # Get table name
        table_name = self.table_name.get().strip()
        if not table_name:
            table_name = "new_table"

        # Build column definitions
        column_defs = []
        for i in range(1, self.col_count):
            name_var = getattr(self, f"col_{i}_name")
            type_var = getattr(self, f"col_{i}_type")
            pk_var = getattr(self, f"col_{i}_pk")
            nn_var = getattr(self, f"col_{i}_nn")
            uq_var = getattr(self, f"col_{i}_uq")

            col_name = name_var.get() if hasattr(name_var, "get") else self.sheet.heading(f"col{i}")["text"]
            col_type = type_var.get()

            constraints = []
            if pk_var.get():
                constraints.append("PRIMARY KEY")
            if nn_var.get():
                constraints.append("NOT NULL")
            if uq_var.get():
                constraints.append("UNIQUE")

            column_def = f"    {col_name} {col_type}"
            if constraints:
                column_def += " " + " ".join(constraints)
            column_defs.append(column_def)

        # Generate CREATE TABLE statement
        sql = f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(column_defs)
        sql += "\n);"

        # Update preview
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, sql)

    def get_column_definitions(self) -> List[str]:
        """Get column definitions for table creation."""
        column_defs = []
        for i in range(1, self.col_count):
            name_var = getattr(self, f"col_{i}_name")
            type_var = getattr(self, f"col_{i}_type")
            pk_var = getattr(self, f"col_{i}_pk")
            nn_var = getattr(self, f"col_{i}_nn")
            uq_var = getattr(self, f"col_{i}_uq")

            col_name = name_var.get() if hasattr(name_var, "get") else self.sheet.heading(f"col{i}")["text"]
            col_type = type_var.get()

            constraints = []
            if pk_var.get():
                constraints.append("PRIMARY KEY")
            if nn_var.get():
                constraints.append("NOT NULL")
            if uq_var.get():
                constraints.append("UNIQUE")

            column_def = f"{col_name} {col_type}"
            if constraints:
                column_def += " " + " ".join(constraints)
            column_defs.append(column_def)

        return column_defs

    def create_table(self):
        """Create the table in the database."""
        table_name = self.table_name.get().strip()
        if not table_name:
            messagebox.showerror("Error", "Table name is required.")
            return

        column_defs = self.get_column_definitions()
        if not column_defs:
            messagebox.showerror("Error", "At least one column is required.")
            return

        try:
            self.db_manager.create_table(table_name, column_defs)
            messagebox.showinfo("Success", f"Table '{table_name}' created successfully!")

            # Call callback if provided
            if self.on_table_created:
                self.on_table_created()

            self.dialog.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to create table: {str(e)}")

class ExcelDataEditor:
    """Excel-like interface for editing table data."""

    def __init__(self, parent, db_manager: DatabaseManager, table_name: str):
        """
        Initialize the Excel-like data editor.

        Args:
            parent: Parent tkinter widget
            db_manager: DatabaseManager instance
            table_name: Name of the table to edit
        """
        self.parent = parent
        self.db_manager = db_manager
        self.table_name = table_name

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Data: {table_name}")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Configure row and column weights
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)

        # Create frame for spreadsheet
        self.sheet_frame = ttk.Frame(self.dialog)
        self.sheet_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create the treeview with scrollbars
        self.sheet = ttk.Treeview(self.sheet_frame)

        vsb = ttk.Scrollbar(self.sheet_frame, orient="vertical", command=self.sheet.yview)
        self.sheet.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(self.sheet_frame, orient="horizontal", command=self.sheet.xview)
        self.sheet.configure(xscrollcommand=hsb.set)

        # Place the scrollbars
        self.sheet.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure weights in sheet_frame
        self.sheet_frame.grid_columnconfigure(0, weight=1)
        self.sheet_frame.grid_rowconfigure(0, weight=1)

        # Add buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ttk.Button(btn_frame, text="Add Row", command=self.add_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Save Changes", command=self.save_changes).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(btn_frame, text="Close", command=self.dialog.destroy).pack(
            side=tk.RIGHT, padx=5
        )

        # Initialize the sheet and load data
        self.initialize_sheet()

        # Setup cell editing
        self.setup_cell_editing()

    def initialize_sheet(self):
        """Initialize the sheet and load data."""
        try:
            # Get table structure
            schema = self.db_manager.get_table_schema(self.table_name)
            self.columns = []

            for col_info in schema:
                col_name = col_info[1]  # Column name
                self.columns.append(col_name)

            # Setup treeview columns
            self.sheet["columns"] = self.columns

            # Hide first column
            self.sheet.column("#0", width=0, stretch=tk.NO)
            self.sheet.heading("#0", text="")

            # Configure column properties
            for col_name in self.columns:
                self.sheet.column(col_name, width=100, minwidth=50)
                self.sheet.heading(col_name, text=col_name)

            # Load data
            query = f"SELECT * FROM {self.table_name}"
            rows = self.db_manager.execute_query(query)

            for row in rows:
                self.sheet.insert("", tk.END, text="", values=row)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load table data: {str(e)}")
            self.dialog.destroy()

    def setup_cell_editing(self):
        """Setup cell editing functionality."""
        self.edited_cell = None
        self.cell_editor = None

        def on_double_click(event):
            region = self.sheet.identify("region", event.x, event.y)
            if region != "cell":
                return

            column = self.sheet.identify_column(event.x)
            row = self.sheet.identify_row(event.y)

            if not row or not column:
                return

            # Get column index (remove # from column)
            col_idx = int(column[1:]) - 1
            if col_idx < 0 or col_idx >= len(self.columns):
                return

            col_name = self.columns[col_idx]

            # Get current value
            values = self.sheet.item(row, "values")
            current_value = values[col_idx] if values and len(values) > col_idx else ""

            # Get cell coordinates
            x, y, width, height = self.sheet.bbox(row, column)

            # Create and position entry widget
            entry = ttk.Entry(self.sheet)
            entry.insert(0, str(current_value) if current_value is not None else "")
            entry.select_range(0, tk.END)
            entry.focus()

            def on_entry_return(event):
                new_value = entry.get()
                values = list(self.sheet.item(row, "values"))
                values[col_idx] = new_value
                self.sheet.item(row, values=values)
                entry.destroy()

            entry.bind("<Return>", on_entry_return)
            entry.bind("<Escape>", lambda e: entry.destroy())
            entry.bind("<FocusOut>", lambda e: entry.destroy())

            entry.place(x=x, y=y, width=width, height=height)
            self.cell_editor = entry

        self.sheet.bind("<Double-1>", on_double_click)

    def add_row(self):
        """Add a new row to the sheet."""
        values = [""] * len(self.columns)
        self.sheet.insert("", tk.END, text="", values=values)

    def delete_selected(self):
        """Delete selected rows."""
        selection = self.sheet.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a row to delete.")
            return

        # Delete selected rows
        for item in selection:
            self.sheet.delete(item)

    def save_changes(self):
        """Save changes to the database."""
        try:
            # First, clear the table
            self.db_manager.execute_query(f"DELETE FROM {self.table_name}")

            # Insert all rows
            rows = []
            for item in self.sheet.get_children():
                values = self.sheet.item(item, "values")
                row_data = {}
                for i, col_name in enumerate(self.columns):
                    if i < len(values):
                        # Handle empty strings as NULL for non-TEXT columns
                        value = values[i]
                        if value == "":
                            value = None
                        row_data[col_name] = value
                rows.append(row_data)

            # Use batch insert
            if rows:
                self.db_manager.batch_insert(self.table_name, rows)

            messagebox.showinfo("Success", "Changes saved successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")
