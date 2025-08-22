"""
Text file import wizard for database creator application.
Provides a 4-step wizard interface for importing CSV, TSV, and other text-based files.
"""
import os
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from typing import List, Dict, Any, Optional

from .db_import_export import DatabaseImportExport


class TextImportWizard:
    """4-step wizard for importing text files into database."""
    
    def __init__(self, parent, db_path: str):
        """Initialize the import wizard.
        
        Args:
            parent: Parent window
            db_path: Path to the database file
        """
        self.parent = parent
        self.db_path = db_path
        
        # Wizard state
        self.current_step = 0
        self.file_path = ""
        self.file_type = "csv"
        self.table_name = ""
        self.delimiter = ","
        self.has_header = True
        self.encoding = "utf-8"
        self.sample_data = []
        self.headers = []
        self.column_types = {}
        self.column_constraints = {}
        
        # Create wizard window
        self.window = tk.Toplevel(parent)
        self.window.title("Text File Import Wizard")
        self.window.geometry("800x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_ui()
        self.show_step(0)
    
    def setup_ui(self):
        """Setup the wizard UI."""
        # Main frame
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="Text File Import Wizard",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Step indicator
        self.step_frame = ttk.Frame(self.main_frame)
        self.step_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.step_labels = []
        steps = ["File Selection", "Preview Data", "Column Mapping", "Import Options"]
        for i, step in enumerate(steps):
            label = ttk.Label(self.step_frame, text=f"{i+1}. {step}")
            label.pack(side=tk.LEFT, padx=20)
            self.step_labels.append(label)
        
        # Content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.prev_button = ttk.Button(
            self.button_frame,
            text="Previous",
            command=self.prev_step,
            state="disabled"
        )
        self.prev_button.pack(side=tk.LEFT)
        
        self.next_button = ttk.Button(
            self.button_frame,
            text="Next",
            command=self.next_step
        )
        self.next_button.pack(side=tk.RIGHT)
        
        self.cancel_button = ttk.Button(
            self.button_frame,
            text="Cancel",
            command=self.cancel
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def show_step(self, step_num: int):
        """Show the specified step."""
        self.current_step = step_num
        
        # Update step indicator
        for i, label in enumerate(self.step_labels):
            if i == step_num:
                label.config(foreground="blue", font=("Arial", 10, "bold"))
            elif i < step_num:
                label.config(foreground="green")
            else:
                label.config(foreground="gray")
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show step content
        if step_num == 0:
            self.show_file_selection()
        elif step_num == 1:
            self.show_preview_data()
        elif step_num == 2:
            self.show_column_mapping()
        elif step_num == 3:
            self.show_import_options()
        
        # Update button states
        self.prev_button.config(state="normal" if step_num > 0 else "disabled")
        
        if step_num == 3:
            self.next_button.config(text="Import", command=self.start_import)
        else:
            self.next_button.config(text="Next", command=self.next_step)
    
    def show_file_selection(self):
        """Show file selection step."""
        # File type selection
        type_frame = ttk.LabelFrame(self.content_frame, text="File Type")
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_type_var = tk.StringVar(value=self.file_type)
        
        ttk.Radiobutton(
            type_frame,
            text="CSV (Comma-separated)",
            variable=self.file_type_var,
            value="csv"
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Radiobutton(
            type_frame,
            text="TSV (Tab-separated)",
            variable=self.file_type_var,
            value="tsv"
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Radiobutton(
            type_frame,
            text="Custom delimiter",
            variable=self.file_type_var,
            value="custom"
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # File selection
        file_frame = ttk.LabelFrame(self.content_frame, text="File Selection")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path_var = tk.StringVar(value=self.file_path)
        
        file_inner = ttk.Frame(file_frame)
        file_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(file_inner, text="File:").pack(anchor=tk.W)
        
        file_row = ttk.Frame(file_inner)
        file_row.pack(fill=tk.X, pady=(5, 0))
        
        self.file_entry = ttk.Entry(file_row, textvariable=self.file_path_var)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            file_row,
            text="Browse",
            command=self.browse_file
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Table name
        table_frame = ttk.LabelFrame(self.content_frame, text="Table Name")
        table_frame.pack(fill=tk.X)
        
        self.table_name_var = tk.StringVar(value=self.table_name)
        
        table_inner = ttk.Frame(table_frame)
        table_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(table_inner, text="Table name:").pack(anchor=tk.W)
        
        self.table_entry = ttk.Entry(table_inner, textvariable=self.table_name_var)
        self.table_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Auto-generate table name from filename
        if self.file_path and not self.table_name:
            filename = os.path.basename(self.file_path)
            name_without_ext = os.path.splitext(filename)[0]
            clean_name = ''.join(c if c.isalnum() else '_' for c in name_without_ext)
            self.table_name_var.set(clean_name)
    
    def show_preview_data(self):
        """Show data preview step."""
        # Delimiter configuration
        delimiter_frame = ttk.LabelFrame(self.content_frame, text="Delimiter Configuration")
        delimiter_frame.pack(fill=tk.X, pady=(0, 10))
        
        del_inner = ttk.Frame(delimiter_frame)
        del_inner.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(del_inner, text="Delimiter:").pack(side=tk.LEFT)
        
        self.delimiter_var = tk.StringVar()
        self.delimiter_entry = ttk.Entry(del_inner, textvariable=self.delimiter_var, width=5)
        self.delimiter_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Set default delimiter based on file type
        file_type = self.file_type_var.get()
        if file_type == "csv":
            self.delimiter_var.set(",")
        elif file_type == "tsv":
            self.delimiter_var.set("\\t")
        else:
            self.delimiter_var.set(self.delimiter)
        
        self.has_header_var = tk.BooleanVar(value=self.has_header)
        ttk.Checkbutton(
            del_inner,
            text="First row contains headers",
            variable=self.has_header_var
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Button(
            del_inner,
            text="Refresh Preview",
            command=self.refresh_preview
        ).pack(side=tk.RIGHT)
        
        # Encoding selection
        encoding_frame = ttk.Frame(del_inner)
        encoding_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Label(encoding_frame, text="Encoding:").pack(side=tk.LEFT)
        
        self.encoding_var = tk.StringVar(value=self.encoding)
        encoding_combo = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding_var,
            values=["utf-8", "latin-1", "cp1252", "utf-16"],
            width=10,
            state="readonly"
        )
        encoding_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Data preview
        preview_frame = ttk.LabelFrame(self.content_frame, text="Data Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for preview
        self.preview_tree = ttk.Treeview(preview_frame)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        
        self.preview_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack treeview and scrollbars
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load preview data
        self.refresh_preview()
    
    def show_column_mapping(self):
        """Show column mapping step."""
        # Create scrollable frame
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Column mapping header
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Column", width=20, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Data Type", width=15, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Constraints", width=30, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # Column mappings
        self.column_widgets = {}
        
        for i, header in enumerate(self.headers):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            
            # Column name
            ttk.Label(frame, text=header, width=20).pack(side=tk.LEFT)
            
            # Data type
            type_var = tk.StringVar()
            type_combo = ttk.Combobox(
                frame,
                textvariable=type_var,
                values=["TEXT", "INTEGER", "REAL", "BOOLEAN", "DATE", "DATETIME"],
                width=12,
                state="readonly"
            )
            type_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # Auto-detect type based on sample data
            detected_type = self.detect_column_type(i)
            type_var.set(detected_type)
            
            # Constraints frame
            constraints_frame = ttk.Frame(frame)
            constraints_frame.pack(side=tk.LEFT)
            
            pk_var = tk.BooleanVar()
            nn_var = tk.BooleanVar()
            uq_var = tk.BooleanVar()
            
            ttk.Checkbutton(constraints_frame, text="Primary Key", variable=pk_var).pack(side=tk.LEFT)
            ttk.Checkbutton(constraints_frame, text="Not Null", variable=nn_var).pack(side=tk.LEFT, padx=(10, 0))
            ttk.Checkbutton(constraints_frame, text="Unique", variable=uq_var).pack(side=tk.LEFT, padx=(10, 0))
            
            self.column_widgets[header] = {
                'type': type_var,
                'pk': pk_var,
                'nn': nn_var,
                'uq': uq_var
            }
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_import_options(self):
        """Show import options step."""
        # Import summary
        summary_frame = ttk.LabelFrame(self.content_frame, text="Import Summary")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        summary_text = f"""
File: {self.file_path}
Table: {self.table_name_var.get()}
Rows to import: {len(self.sample_data)} (sample)
Columns: {len(self.headers)}
Delimiter: {self.delimiter_var.get().replace(chr(9), '\\t')}
Encoding: {self.encoding_var.get()}
        """.strip()
        
        ttk.Label(summary_frame, text=summary_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Import options
        options_frame = ttk.LabelFrame(self.content_frame, text="Import Options")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.skip_errors_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Skip rows with errors",
            variable=self.skip_errors_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        self.batch_size_var = tk.IntVar(value=1000)
        batch_frame = ttk.Frame(options_frame)
        batch_frame.pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Label(batch_frame, text="Batch size:").pack(side=tk.LEFT)
        ttk.Entry(batch_frame, textvariable=self.batch_size_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress frame (initially hidden)
        self.progress_frame = ttk.LabelFrame(self.content_frame, text="Import Progress")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready to import...")
    
    def browse_file(self):
        """Browse for file to import."""
        filetypes = [
            ("Text Files", "*.csv *.tsv *.txt"),
            ("CSV Files", "*.csv"),
            ("TSV Files", "*.tsv"),
            ("All Files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        
        if file_path:
            self.file_path_var.set(file_path)
            
            # Auto-generate table name
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            clean_name = ''.join(c if c.isalnum() else '_' for c in name_without_ext)
            self.table_name_var.set(clean_name)
            
            # Auto-detect file type
            if file_path.lower().endswith('.tsv'):
                self.file_type_var.set("tsv")
            elif file_path.lower().endswith('.csv'):
                self.file_type_var.set("csv")
    
    def refresh_preview(self):
        """Refresh the data preview."""
        if not self.file_path_var.get():
            return
        
        try:
            # Get delimiter
            delimiter = self.delimiter_var.get()
            if delimiter == "\\t":
                delimiter = "\t"
            
            # Read sample data
            encoding = self.encoding_var.get()
            
            with open(self.file_path_var.get(), 'r', encoding=encoding) as file:
                # Detect delimiter if not specified
                if not delimiter or delimiter == "auto":
                    sample = file.read(1024)
                    file.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.reader(file, delimiter=delimiter)
                rows = []
                
                for i, row in enumerate(reader):
                    rows.append(row)
                    if i >= 10:  # Limit preview to 10 rows
                        break
                
                if not rows:
                    messagebox.showerror("Error", "No data found in file")
                    return
                
                # Determine headers
                has_header = self.has_header_var.get()
                if has_header:
                    self.headers = rows[0]
                    self.sample_data = rows[1:]
                else:
                    self.headers = [f"Column_{i+1}" for i in range(len(rows[0]))]
                    self.sample_data = rows
                
                # Update preview tree
                self.preview_tree.delete(*self.preview_tree.get_children())
                
                # Configure columns
                self.preview_tree["columns"] = self.headers
                self.preview_tree["show"] = "headings"
                
                for header in self.headers:
                    self.preview_tree.heading(header, text=header)
                    self.preview_tree.column(header, width=100)
                
                # Add sample data
                for row in self.sample_data:
                    # Pad row if necessary
                    padded_row = row + [""] * (len(self.headers) - len(row))
                    self.preview_tree.insert("", "end", values=padded_row[:len(self.headers)])
                
                # Store values for next steps
                self.delimiter = delimiter
                self.has_header = has_header
                self.encoding = encoding
                
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file: {str(e)}")
    
    def detect_column_type(self, col_index: int) -> str:
        """Detect column data type based on sample data."""
        if col_index >= len(self.headers) or not self.sample_data:
            return "TEXT"
        
        # Get sample values for this column
        values = []
        for row in self.sample_data:
            if col_index < len(row) and row[col_index].strip():
                values.append(row[col_index].strip())
        
        if not values:
            return "TEXT"
        
        # Check if all values are integers
        try:
            for value in values:
                int(value)
            return "INTEGER"
        except ValueError:
            pass
        
        # Check if all values are floats
        try:
            for value in values:
                float(value)
            return "REAL"
        except ValueError:
            pass
        
        # Check if all values are booleans
        bool_values = {"true", "false", "1", "0", "yes", "no", "y", "n"}
        if all(value.lower() in bool_values for value in values):
            return "BOOLEAN"
        
        return "TEXT"
    
    def next_step(self):
        """Go to next step."""
        if self.current_step == 0:
            # Validate file selection
            if not self.file_path_var.get():
                messagebox.showerror("Error", "Please select a file")
                return
            
            if not self.table_name_var.get():
                messagebox.showerror("Error", "Please enter a table name")
                return
            
            self.file_path = self.file_path_var.get()
            self.file_type = self.file_type_var.get()
            self.table_name = self.table_name_var.get()
        
        elif self.current_step == 1:
            # Validate preview
            if not self.headers:
                messagebox.showerror("Error", "No data preview available. Please check your file and delimiter settings.")
                return
        
        elif self.current_step == 2:
            # Store column mappings
            for header, widgets in self.column_widgets.items():
                self.column_types[header] = widgets['type'].get()
                self.column_constraints[header] = {
                    'pk': widgets['pk'].get(),
                    'nn': widgets['nn'].get(),
                    'uq': widgets['uq'].get()
                }
        
        if self.current_step < 3:
            self.show_step(self.current_step + 1)
    
    def prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def start_import(self):
        """Start the import process."""
        # Show progress frame
        self.progress_frame.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.progress_label.pack(padx=10, pady=(0, 10))
        
        # Disable buttons
        self.next_button.config(state="disabled")
        self.prev_button.config(state="disabled")
        
        # Start import in separate thread
        import_thread = threading.Thread(target=self.import_data)
        import_thread.daemon = True
        import_thread.start()
    
    def import_data(self):
        """Import the data (runs in separate thread)."""
        try:
            # Update progress
            self.window.after(0, lambda: self.progress_label.config(text="Preparing import..."))
            self.window.after(0, lambda: self.progress_var.set(10))
            
            # Create custom CSV import with column types and constraints
            success, message = self.import_csv_with_types()
            
            self.window.after(0, lambda: self.progress_var.set(100))
            
            if success:
                self.window.after(0, lambda: self.progress_label.config(text="Import completed successfully!"))
                self.window.after(0, lambda: messagebox.showinfo("Success", message))
                self.window.after(0, self.close_wizard)
            else:
                self.window.after(0, lambda: self.progress_label.config(text="Import failed"))
                self.window.after(0, lambda: messagebox.showerror("Error", message))
                self.window.after(0, self.enable_buttons)
        
        except Exception as e:
            self.window.after(0, lambda: self.progress_label.config(text="Import failed"))
            self.window.after(0, lambda: messagebox.showerror("Error", f"Import error: {str(e)}"))
            self.window.after(0, self.enable_buttons)
    
    def import_csv_with_types(self):
        """Import CSV with custom column types and constraints."""
        try:
            from .db_connections import DatabaseConnection
            
            # Connect to database
            conn = DatabaseConnection.connect_sqlite(self.db_path)
            if not conn:
                return False, "Failed to connect to database"
            
            cursor = conn.cursor()
            
            # Create table with proper column types and constraints
            column_defs = []
            for header in self.headers:
                col_type = self.column_types.get(header, "TEXT")
                constraints = []
                
                if self.column_constraints.get(header, {}).get('pk'):
                    constraints.append("PRIMARY KEY")
                if self.column_constraints.get(header, {}).get('nn'):
                    constraints.append("NOT NULL")
                if self.column_constraints.get(header, {}).get('uq'):
                    constraints.append("UNIQUE")
                
                # Sanitize column name
                clean_header = ''.join(c if c.isalnum() else '_' for c in header)
                
                column_def = f"{clean_header} {col_type}"
                if constraints:
                    column_def += " " + " ".join(constraints)
                
                column_defs.append(column_def)
            
            create_stmt = f"CREATE TABLE IF NOT EXISTS {self.table_name} ("
            create_stmt += ", ".join(column_defs)
            create_stmt += ")"
            
            cursor.execute(create_stmt)
            
            # Import data
            delimiter = self.delimiter
            if delimiter == "\\t":
                delimiter = "\t"
            
            with open(self.file_path, 'r', encoding=self.encoding) as file:
                reader = csv.reader(file, delimiter=delimiter)
                
                # Skip header if present
                if self.has_header:
                    next(reader)
                
                # Import data in batches
                batch_size = self.batch_size_var.get()
                batch = []
                row_count = 0
                error_count = 0
                
                for row in reader:
                    try:
                        # Ensure row has the right number of columns
                        padded_row = row + [None] * (len(self.headers) - len(row))
                        batch.append(padded_row[:len(self.headers)])
                        
                        if len(batch) >= batch_size:
                            self.insert_batch(cursor, batch)
                            row_count += len(batch)
                            batch = []
                            
                            # Update progress
                            progress = min(90, (row_count / 10000) * 80 + 10)
                            self.window.after(0, lambda p=progress: self.progress_var.set(p))
                            self.window.after(0, lambda r=row_count: self.progress_label.config(
                                text=f"Imported {r} rows..."
                            ))
                    
                    except Exception as e:
                        error_count += 1
                        if not self.skip_errors_var.get():
                            raise e
                
                # Insert remaining batch
                if batch:
                    self.insert_batch(cursor, batch)
                    row_count += len(batch)
            
            conn.commit()
            conn.close()
            
            message = f"Successfully imported {row_count} rows into table '{self.table_name}'"
            if error_count > 0:
                message += f" ({error_count} rows skipped due to errors)"
            
            return True, message
        
        except Exception as e:
            return False, f"Import error: {str(e)}"
    
    def insert_batch(self, cursor, batch):
        """Insert a batch of rows."""
        if not batch:
            return
        
        placeholders = ", ".join(["?"] * len(self.headers))
        cursor.executemany(
            f"INSERT INTO {self.table_name} VALUES ({placeholders})",
            batch
        )
    
    def enable_buttons(self):
        """Re-enable buttons after import failure."""
        self.next_button.config(state="normal")
        self.prev_button.config(state="normal")
    
    def close_wizard(self):
        """Close the wizard."""
        self.window.destroy()
    
    def cancel(self):
        """Cancel the wizard."""
        self.window.destroy()


def show_text_import_wizard(parent, db_path: str):
    """Show the text import wizard.
    
    Args:
        parent: Parent window
        db_path: Path to the database file
    """
    wizard = TextImportWizard(parent, db_path)
    return wizard