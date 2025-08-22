"""
Data analytics and visualization module for the Database Creator tool.

This module provides functionality for:
1. Running SQL queries against databases
2. Visualizing results with various chart types
3. Exporting analysis to different formats
4. Interactive data exploration
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import json
import threading
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from datetime import datetime

# Import local modules
from .config import DB_STORAGE_DIR, ensure_directory_exists, load_config, save_config

class SQLAnalyticsTab:
    def __init__(self, parent, main_app):
        """
        Initialize the SQL Analytics tab.

        Args:
            parent: The parent notebook widget
            main_app: The main application instance
        """
        self.main_app = main_app
        self.parent = parent

        # Create the main tab frame
        self.tab = ttk.Frame(parent)

        # Create the paned window for resizable sections
        self.paned_window = ttk.PanedWindow(self.tab, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left side - Controls and query input
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)

        # Right side - Results and visualization
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=2)

        # Current connection info
        self.connection = None
        self.current_db_path = None
        self.current_db_type = "sqlite"  # Default

        # Setup UI components
        self._create_database_selector()
        self._create_query_editor()
        self._create_results_area()
        self._create_visualization_area()

    def _create_database_selector(self):
        """Create the database selection area"""
        db_frame = ttk.LabelFrame(self.left_frame, text="Database Connection")
        db_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)

        # Database connection dropdown
        ttk.Label(db_frame, text="Select Database:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Combobox for database selection
        self.db_var = tk.StringVar()
        self.db_combo = ttk.Combobox(db_frame, textvariable=self.db_var, state="readonly")
        self.db_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.db_combo.bind("<<ComboboxSelected>>", self.on_database_selected)

        # Refresh button
        refresh_btn = ttk.Button(db_frame, text="↻", width=3, command=self.refresh_databases)
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)

        # Connection info
        self.conn_info = ttk.Label(db_frame, text="No database selected")
        self.conn_info.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        # Configure grid
        db_frame.columnconfigure(1, weight=1)

        # Load the databases
        self.refresh_databases()

    def _create_query_editor(self):
        """Create the SQL query editor area"""
        query_frame = ttk.LabelFrame(self.left_frame, text="SQL Query")
        query_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Query text area with syntax highlighting (basic for now)
        self.query_text = tk.Text(query_frame, wrap=tk.WORD, height=15,
                                 font=("Consolas", 11))
        self.query_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add some basic SQL syntax highlighting (could be enhanced with a proper library)
        self.query_text.tag_configure("keyword", foreground="blue", font=("Consolas", 11, "bold"))
        self.query_text.tag_configure("function", foreground="purple")
        self.query_text.tag_configure("string", foreground="green")
        self.query_text.tag_configure("comment", foreground="grey", font=("Consolas", 11, "italic"))

        # Example query
        example_query = """-- Example SQL query
SELECT
    column1,
    COUNT(*) as count,
    AVG(column2) as average
FROM table_name
WHERE column3 > 100
GROUP BY column1
ORDER BY count DESC
LIMIT 10;
"""
        self.query_text.insert(tk.END, example_query)

        # Button frame
        btn_frame = ttk.Frame(query_frame)
        btn_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)

        # Run query button
        run_btn = ttk.Button(btn_frame, text="Run Query", command=self.run_query)
        run_btn.pack(side=tk.LEFT, padx=5)

        # Clear button
        clear_btn = ttk.Button(btn_frame, text="Clear", command=lambda: self.query_text.delete(1.0, tk.END))
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Sample queries dropdown
        ttk.Label(btn_frame, text="Sample queries:").pack(side=tk.LEFT, padx=(15, 5))
        self.sample_var = tk.StringVar()
        sample_combo = ttk.Combobox(btn_frame, textvariable=self.sample_var, state="readonly", width=25)
        sample_combo['values'] = [
            "Select all data",
            "Count records by group",
            "Complex aggregation",
            "Join tables",
            "Advanced analytics"
        ]
        sample_combo.pack(side=tk.LEFT, padx=5)
        sample_combo.bind("<<ComboboxSelected>>", self.load_sample_query)

    def _create_results_area(self):
        """Create the results display area"""
        results_frame = ttk.LabelFrame(self.right_frame, text="Query Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Notebook for different result views
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Data Grid
        self.data_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.data_frame, text="Data Grid")

        # Treeview for data display
        self.results_tree = ttk.Treeview(self.data_frame)
        tree_scroll_y = ttk.Scrollbar(self.data_frame, orient="vertical", command=self.results_tree.yview)
        tree_scroll_x = ttk.Scrollbar(self.data_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        # Pack the scrollbars and treeview
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.results_tree.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Raw Data
        self.raw_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.raw_frame, text="Raw Data")

        # Text widget for raw data display
        self.raw_text = tk.Text(self.raw_frame, wrap=tk.NONE, font=("Consolas", 10))
        raw_scroll_y = ttk.Scrollbar(self.raw_frame, orient="vertical", command=self.raw_text.yview)
        raw_scroll_x = ttk.Scrollbar(self.raw_frame, orient="horizontal", command=self.raw_text.xview)
        self.raw_text.configure(yscrollcommand=raw_scroll_y.set, xscrollcommand=raw_scroll_x.set)

        # Pack the scrollbars and text widget
        raw_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        raw_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.raw_text.pack(fill=tk.BOTH, expand=True)

        # Tab 3: Statistics
        self.stats_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.stats_frame, text="Statistics")

        # Add a text widget for statistics
        self.stats_text = tk.Text(self.stats_frame, wrap=tk.WORD, font=("Consolas", 10))
        stats_scroll = ttk.Scrollbar(self.stats_frame, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)

        # Pack the scrollbar and text widget
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Results info bar
        self.results_info = ttk.Label(results_frame, text="No query results")
        self.results_info.pack(fill=tk.X, padx=5, pady=5)

    def _create_visualization_area(self):
        """Create the visualization area"""
        viz_frame = ttk.LabelFrame(self.right_frame, text="Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls frame
        controls_frame = ttk.Frame(viz_frame)
        controls_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)

        # Chart type selector
        ttk.Label(controls_frame, text="Chart type:").pack(side=tk.LEFT, padx=5)
        self.chart_var = tk.StringVar(value="Bar Chart")
        chart_combo = ttk.Combobox(controls_frame, textvariable=self.chart_var, state="readonly", width=15)
        chart_combo['values'] = [
            "Bar Chart",
            "Line Chart",
            "Pie Chart",
            "Scatter Plot",
            "Histogram",
            "Box Plot",
            "Heat Map"
        ]
        chart_combo.pack(side=tk.LEFT, padx=5)

        # X-axis selector
        ttk.Label(controls_frame, text="X-axis:").pack(side=tk.LEFT, padx=(15, 5))
        self.x_axis_var = tk.StringVar()
        self.x_axis_combo = ttk.Combobox(controls_frame, textvariable=self.x_axis_var, state="readonly", width=15)
        self.x_axis_combo.pack(side=tk.LEFT, padx=5)

        # Y-axis selector
        ttk.Label(controls_frame, text="Y-axis:").pack(side=tk.LEFT, padx=(15, 5))
        self.y_axis_var = tk.StringVar()
        self.y_axis_combo = ttk.Combobox(controls_frame, textvariable=self.y_axis_var, state="readonly", width=15)
        self.y_axis_combo.pack(side=tk.LEFT, padx=5)

        # Generate visualization button
        viz_btn = ttk.Button(controls_frame, text="Generate Visualization", command=self.generate_visualization)
        viz_btn.pack(side=tk.LEFT, padx=(15, 5))

        # Save visualization button
        save_viz_btn = ttk.Button(controls_frame, text="Save Chart", command=self.save_visualization)
        save_viz_btn.pack(side=tk.LEFT, padx=5)

        # Canvas for matplotlib
        self.figure_frame = ttk.Frame(viz_frame)
        self.figure_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create an initial figure and canvas
        self.fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar
        toolbar_frame = ttk.Frame(viz_frame)
        toolbar_frame.pack(fill=tk.X, expand=False)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Current data for visualizations
        self.current_data = None

    def refresh_databases(self):
        """Refresh the list of available databases"""
        self.db_combo['values'] = []
        db_list = []

        # Add SQLite databases from the storage directory
        if os.path.exists(DB_STORAGE_DIR):
            sqlite_dbs = [
                f for f in os.listdir(DB_STORAGE_DIR)
                if f.endswith('.db') and os.path.isfile(os.path.join(DB_STORAGE_DIR, f))
            ]
            db_list.extend([(name, "sqlite") for name in sqlite_dbs])

        # Add external database connections from config
        config = load_config()
        external_connections = config.get("external_connections", {})
        for name, conn_info in external_connections.items():
            db_type = conn_info.get("type", "unknown")
            db_list.append((f"[{db_type.upper()}] {name}", db_type))

        # Update the combobox
        if db_list:
            # Format as "name (type)" for display but store tuple of (name, type) for backend
            self.db_options = db_list
            self.db_combo['values'] = [f"{name}" for name, _ in db_list]
        else:
            self.db_combo['values'] = ["No databases available"]
            self.db_options = []

        # Reset connection info
        if self.connection:
            self.close_connection()
        self.conn_info.config(text="No database selected")

    def on_database_selected(self, event):
        """Handle database selection change"""
        if not self.db_options:
            return

        selected_idx = self.db_combo.current()
        if selected_idx < 0 or selected_idx >= len(self.db_options):
            return

        # Get the selected database info
        db_name, db_type = self.db_options[selected_idx]

        # Close any existing connection
        if self.connection:
            self.close_connection()

        # Connect to the selected database
        try:
            if db_type == "sqlite":
                # For SQLite, we connect directly to the file
                db_path = os.path.join(DB_STORAGE_DIR, db_name)
                self.connection = sqlite3.connect(db_path)
                self.current_db_path = db_path
                self.current_db_type = "sqlite"

                # Display info about the database
                cursor = self.connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                table_count = len(tables)
                table_list = ", ".join([t[0] for t in tables[:5]])
                if table_count > 5:
                    table_list += f"... and {table_count - 5} more"

                self.conn_info.config(
                    text=f"Connected to SQLite: {db_name}\nTables: {table_list}"
                )
            else:
                # For external databases, we get connection info from config
                config = load_config()
                # Extract the actual name from the formatted display string
                # Format is "[TYPE] name"
                actual_name = db_name[db_name.find("]")+2:] if "]" in db_name else db_name

                conn_info = config.get("external_connections", {}).get(actual_name)
                if not conn_info:
                    messagebox.showerror(
                        "Connection Error",
                        f"Could not find connection information for {actual_name}"
                    )
                    return

                self.current_db_type = conn_info.get("type")

                # Connect based on database type
                if self.current_db_type == "mysql":
                    import pymysql
                    self.connection = pymysql.connect(
                        host=conn_info.get("host", "localhost"),
                        user=conn_info.get("user", ""),
                        password=conn_info.get("password", ""),
                        database=conn_info.get("database", ""),
                        port=conn_info.get("port", 3306)
                    )
                    self.current_db_path = f"{conn_info.get('host')}/{conn_info.get('database')}"
                elif self.current_db_type == "postgresql":
                    import psycopg2
                    self.connection = psycopg2.connect(
                        host=conn_info.get("host", "localhost"),
                        user=conn_info.get("user", ""),
                        password=conn_info.get("password", ""),
                        dbname=conn_info.get("database", ""),
                        port=conn_info.get("port", 5432)
                    )
                    self.current_db_path = f"{conn_info.get('host')}/{conn_info.get('database')}"
                else:
                    messagebox.showerror(
                        "Connection Error",
                        f"Unsupported database type: {self.current_db_type}"
                    )
                    return

                # Display connection info
                self.conn_info.config(
                    text=f"Connected to {self.current_db_type.upper()}: {actual_name}\n"
                         f"Host: {conn_info.get('host')}, DB: {conn_info.get('database')}"
                )

            # Show a success message
            self.main_app.set_status(f"Connected to {db_name}")

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.connection = None
            self.current_db_path = None
            self.conn_info.config(text=f"Connection failed: {str(e)}")

    def close_connection(self):
        """Close the current database connection"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
                self.current_db_path = None

    def load_sample_query(self, event):
        """Load a sample query into the editor"""
        selected = self.sample_var.get()

        if selected == "Select all data":
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(tk.END, "-- Get all data from a table\nSELECT * FROM table_name LIMIT 100;")

        elif selected == "Count records by group":
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(tk.END,
                "-- Count records by group\n"
                "SELECT \n"
                "    column_name,\n"
                "    COUNT(*) as count\n"
                "FROM \n"
                "    table_name\n"
                "GROUP BY \n"
                "    column_name\n"
                "ORDER BY \n"
                "    count DESC;"
            )

        elif selected == "Complex aggregation":
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(tk.END,
                "-- Complex aggregation query\n"
                "SELECT \n"
                "    category,\n"
                "    COUNT(*) as count,\n"
                "    AVG(numeric_column) as average,\n"
                "    MIN(numeric_column) as minimum,\n"
                "    MAX(numeric_column) as maximum,\n"
                "    SUM(numeric_column) as total\n"
                "FROM \n"
                "    table_name\n"
                "WHERE \n"
                "    date_column > date('now', '-30 days')\n"
                "GROUP BY \n"
                "    category\n"
                "HAVING \n"
                "    count > 5\n"
                "ORDER BY \n"
                "    average DESC;"
            )

        elif selected == "Join tables":
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(tk.END,
                "-- Join multiple tables\n"
                "SELECT \n"
                "    a.column1,\n"
                "    a.column2,\n"
                "    b.column3,\n"
                "    c.column4\n"
                "FROM \n"
                "    table1 a\n"
                "JOIN \n"
                "    table2 b ON a.id = b.table1_id\n"
                "LEFT JOIN \n"
                "    table3 c ON a.id = c.table1_id\n"
                "WHERE \n"
                "    b.column3 > 100\n"
                "ORDER BY \n"
                "    a.column1;"
            )

        elif selected == "Advanced analytics":
            self.query_text.delete(1.0, tk.END)
            self.query_text.insert(tk.END,
                "-- Advanced analytics query\n"
                "SELECT \n"
                "    strftime('%Y-%m', date_column) as month,\n"
                "    category,\n"
                "    COUNT(*) as count,\n"
                "    SUM(amount) as total_amount,\n"
                "    AVG(amount) as avg_amount,\n"
                "    SUM(amount) * 100.0 / SUM(SUM(amount)) OVER () as percentage\n"
                "FROM \n"
                "    transactions\n"
                "WHERE \n"
                "    date_column >= date('now', '-1 year')\n"
                "GROUP BY \n"
                "    month, category\n"
                "ORDER BY \n"
                "    month, total_amount DESC;"
            )

    def run_query(self):
        """Run the current SQL query"""
        if not self.connection:
            messagebox.showwarning("No Database", "Please select a database first")
            return

        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter an SQL query")
            return

        # Show busy cursor
        self.tab.config(cursor="wait")
        self.main_app.set_status("Running query...")

        # Clear previous results
        self.clear_results()

        # Run query in a separate thread to prevent UI freeze
        threading.Thread(target=self._execute_query, args=(query,), daemon=True).start()

    def _execute_query(self, query):
        """Execute the SQL query in a separate thread"""
        try:
            # Use pandas for data handling
            start_time = datetime.now()
            df = pd.read_sql_query(query, self.connection)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Store the data for later use
            self.current_data = df

            # Update the UI in the main thread
            self.tab.after(0, lambda: self._display_results(df, duration))

        except Exception as e:
            # Show error in the main thread
            self.tab.after(0, lambda: self._display_error(str(e)))

    def _display_results(self, df, duration):
        """Display query results in the UI"""
        try:
            # Reset cursor
            self.tab.config(cursor="")

            # Update status
            row_count = len(df)
            col_count = len(df.columns)
            self.main_app.set_status(f"Query returned {row_count} rows in {duration:.2f} seconds")
            self.results_info.config(
                text=f"Query completed in {duration:.2f} seconds. Results: {row_count} rows, {col_count} columns"
            )

            # Update the data grid
            self._populate_treeview(df)

            # Update raw data view
            self._populate_raw_view(df)

            # Update statistics view
            self._populate_statistics(df)

            # Update visualization options
            self._update_visualization_options(df)

            # Switch to results tab
            self.results_notebook.select(0)  # Select the Data Grid tab

        except Exception as e:
            self._display_error(f"Error displaying results: {str(e)}")

    def _populate_treeview(self, df):
        """Populate the treeview with dataframe contents"""
        # Clear existing data
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Configure columns
        self.results_tree["columns"] = list(df.columns)
        self.results_tree["show"] = "headings"

        # Set column headings
        for col in df.columns:
            # Determine column width based on data type
            if pd.api.types.is_numeric_dtype(df[col]):
                width = 100
            else:
                width = 150
            self.results_tree.column(col, width=width, minwidth=50)
            self.results_tree.heading(col, text=col)

        # Add data rows
        for _, row in df.iterrows():
            # Convert any non-string values to strings
            values = []
            for v in row:
                if pd.isna(v):
                    values.append("")
                else:
                    values.append(str(v))
            self.results_tree.insert("", tk.END, values=values)

    def _populate_raw_view(self, df):
        """Display raw data in text format"""
        self.raw_text.delete(1.0, tk.END)

        # Format as fixed-width text
        if len(df) > 0:
            # Generate header
            header = []
            widths = []

            for col in df.columns:
                # Determine width based on column name and values
                col_width = max(
                    len(str(col)),
                    df[col].astype(str).str.len().max() if len(df) > 0 else 0
                )
                col_width = min(col_width, 30)  # Cap width at 30 chars
                col_width = max(col_width, 5)   # Minimum width of 5 chars

                header.append(str(col).ljust(col_width))
                widths.append(col_width)

            # Add header
            self.raw_text.insert(tk.END, " | ".join(header) + "\n")
            self.raw_text.insert(tk.END, "-|-".join("-" * width for width in widths) + "\n")

            # Add rows
            for _, row in df.iterrows():
                formatted_row = []
                for i, val in enumerate(row):
                    if pd.isna(val):
                        formatted_row.append(" " * widths[i])
                    else:
                        val_str = str(val)
                        if len(val_str) > widths[i]:
                            val_str = val_str[:widths[i]-3] + "..."
                        formatted_row.append(val_str.ljust(widths[i]))

                self.raw_text.insert(tk.END, " | ".join(formatted_row) + "\n")
        else:
            self.raw_text.insert(tk.END, "No data returned")

    def _populate_statistics(self, df):
        """Display statistics for the query results"""
        self.stats_text.delete(1.0, tk.END)

        if len(df) == 0:
            self.stats_text.insert(tk.END, "No data to analyze")
            return

        # Basic info
        self.stats_text.insert(tk.END, f"Dataset Overview:\n")
        self.stats_text.insert(tk.END, f"- Rows: {len(df)}\n")
        self.stats_text.insert(tk.END, f"- Columns: {len(df.columns)}\n\n")

        # Column types
        self.stats_text.insert(tk.END, "Column Types:\n")
        for col in df.columns:
            dtype = df[col].dtype
            self.stats_text.insert(tk.END, f"- {col}: {dtype}\n")
        self.stats_text.insert(tk.END, "\n")

        # Numeric statistics
        num_cols = df.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            self.stats_text.insert(tk.END, "Numeric Column Statistics:\n")
            stats = df[num_cols].describe().transpose()

            for col in stats.index:
                self.stats_text.insert(tk.END, f"- {col}:\n")
                for stat, value in stats.loc[col].items():
                    self.stats_text.insert(tk.END, f"  - {stat}: {value:.4f}\n")
                self.stats_text.insert(tk.END, "\n")

        # Categorical statistics
        cat_cols = df.select_dtypes(exclude=['number']).columns
        if len(cat_cols) > 0:
            self.stats_text.insert(tk.END, "Categorical Column Statistics:\n")
            for col in cat_cols:
                self.stats_text.insert(tk.END, f"- {col}:\n")

                # Count unique values
                unique_count = df[col].nunique()
                self.stats_text.insert(tk.END, f"  - Unique values: {unique_count}\n")

                # Show most common values (up to 5)
                if unique_count < 100:  # Only for reasonably sized categories
                    value_counts = df[col].value_counts().head(5)
                    self.stats_text.insert(tk.END, f"  - Top values:\n")
                    for val, count in value_counts.items():
                        self.stats_text.insert(tk.END, f"    - {val}: {count} ({count/len(df):.1%})\n")

                self.stats_text.insert(tk.END, "\n")

        # Missing data
        missing = df.isnull().sum()
        if missing.sum() > 0:
            self.stats_text.insert(tk.END, "Missing Values:\n")
            for col, count in missing.items():
                if count > 0:
                    self.stats_text.insert(tk.END, f"- {col}: {count} ({count/len(df):.1%})\n")

    def _update_visualization_options(self, df):
        """Update the visualization options based on the dataframe"""
        # Update axis selectors
        columns = list(df.columns)

        self.x_axis_combo['values'] = columns
        self.y_axis_combo['values'] = columns

        # Try to set sensible defaults
        numeric_cols = df.select_dtypes(include=['number']).columns

        if len(columns) > 0:
            self.x_axis_var.set(columns[0])

        if len(numeric_cols) > 0:
            self.y_axis_var.set(numeric_cols[0])

    def _display_error(self, error_message):
        """Display query error"""
        # Reset cursor
        self.tab.config(cursor="")

        # Update status
        self.main_app.set_status("Query failed")
        self.results_info.config(text=f"Query error: {error_message}")

        # Show error in raw view
        self.raw_text.delete(1.0, tk.END)
        self.raw_text.insert(tk.END, f"ERROR: {error_message}")

        # Clear other views
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.stats_text.delete(1.0, tk.END)

        # Switch to raw data tab to show the error
        self.results_notebook.select(1)  # Select the Raw Data tab

    def clear_results(self):
        """Clear all result displays"""
        # Clear treeview
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Clear text widgets
        self.raw_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)

        # Reset info
        self.results_info.config(text="No query results")

        # Clear visualization
        self.fig.clear()
        self.canvas.draw()

        # Reset current data
        self.current_data = None

    def generate_visualization(self):
        """Generate a visualization based on current settings"""
        if self.current_data is None or len(self.current_data) == 0:
            messagebox.showwarning("No Data", "Run a query first to get data to visualize")
            return

        # Get selected options
        chart_type = self.chart_var.get()
        x_col = self.x_axis_var.get()
        y_col = self.y_axis_var.get()

        if not x_col or not y_col:
            messagebox.showwarning("Missing Axes", "Please select columns for X and Y axes")
            return

        # Check if columns exist
        if x_col not in self.current_data.columns or y_col not in self.current_data.columns:
            messagebox.showwarning("Invalid Columns", "Selected columns are not in the dataset")
            return

        # Show busy cursor
        self.tab.config(cursor="wait")
        self.main_app.set_status("Generating visualization...")

        # Clear previous plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        try:
            df = self.current_data

            # Create the appropriate chart
            if chart_type == "Bar Chart":
                # For bar charts, we may want to aggregate data
                if df[x_col].nunique() > 15:
                    # Too many unique values, take top N
                    top_values = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(15).index
                    plot_df = df[df[x_col].isin(top_values)]
                    # Aggregate
                    plot_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                    plot_df = plot_df.sort_values(y_col, ascending=False)
                else:
                    # Aggregate by x column
                    plot_df = df.groupby(x_col)[y_col].sum().reset_index()

                ax.bar(plot_df[x_col], plot_df[y_col])
                ax.set_xticklabels(plot_df[x_col], rotation=45, ha='right')

            elif chart_type == "Line Chart":
                # For line charts, sort by x for connected lines
                plot_df = df.sort_values(x_col)
                ax.plot(plot_df[x_col], plot_df[y_col], marker='o')

                # If x has many values, show fewer tick labels
                if df[x_col].nunique() > 20:
                    # Show only some x tick labels
                    step = max(1, len(plot_df) // 10)
                    indices = range(0, len(plot_df), step)
                    ax.set_xticks([plot_df.iloc[i][x_col] for i in indices])

                ax.set_xticklabels(ax.get_xticks(), rotation=45, ha='right')

            elif chart_type == "Pie Chart":
                # For pie charts, aggregate and show top categories
                if df[x_col].nunique() > 10:
                    # Too many categories, group smaller ones into "Other"
                    counts = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
                    top_n = counts.head(9)
                    other = pd.Series([counts[9:].sum()], index=["Other"])
                    plot_data = pd.concat([top_n, other])
                    labels = plot_data.index
                else:
                    plot_data = df.groupby(x_col)[y_col].sum()
                    labels = plot_data.index

                ax.pie(plot_data, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular

            elif chart_type == "Scatter Plot":
                ax.scatter(df[x_col], df[y_col], alpha=0.6)

            elif chart_type == "Histogram":
                ax.hist(df[y_col], bins=min(20, df[y_col].nunique()))

            elif chart_type == "Box Plot":
                # If x is categorical, group by x
                if df[x_col].nunique() <= 10 and not pd.api.types.is_numeric_dtype(df[x_col]):
                    # Create boxplot grouped by x
                    grouped_data = [df[df[x_col] == val][y_col] for val in df[x_col].unique()]
                    ax.boxplot(grouped_data, labels=df[x_col].unique())
                else:
                    # Single boxplot for y
                    ax.boxplot(df[y_col])
                    ax.set_xticklabels([y_col])

            elif chart_type == "Heat Map":
                # For heatmaps, we need a 2D relationship
                pivot_table = pd.pivot_table(
                    data=df,
                    values=y_col,
                    index=x_col,
                    aggfunc='mean'
                )

                # Only show top N rows if there are too many
                if len(pivot_table) > 15:
                    pivot_table = pivot_table.iloc[:15]

                im = ax.imshow(pivot_table)

                # Customize colorbar and labels
                self.fig.colorbar(im, ax=ax)
                ax.set_yticks(range(len(pivot_table.index)))
                ax.set_yticklabels(pivot_table.index)
                ax.set_xticks([0])
                ax.set_xticklabels([y_col])

            # Set titles and labels
            ax.set_title(f"{chart_type}: {y_col} by {x_col}")
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

            # Add grid for better readability
            ax.grid(True, alpha=0.3)

            # Tight layout for better use of space
            self.fig.tight_layout()

            # Refresh the canvas
            self.canvas.draw()

            # Update status
            self.main_app.set_status(f"Generated {chart_type}")

        except Exception as e:
            messagebox.showerror("Visualization Error", str(e))
            self.main_app.set_status("Visualization failed")

        finally:
            # Reset cursor
            self.tab.config(cursor="")

    def save_visualization(self):
        """Save the current visualization to a file"""
        if self.fig is None:
            messagebox.showwarning("No Visualization", "No visualization to save")
            return

        # Ask for file location
        file_types = [
            ("PNG Image", "*.png"),
            ("PDF Document", "*.pdf"),
            ("SVG Image", "*.svg"),
            ("JPEG Image", "*.jpg")
        ]
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            title="Save Visualization"
        )

        if not file_path:
            return

        try:
            # Save the figure
            self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
            self.main_app.set_status(f"Saved visualization to {file_path}")
            messagebox.showinfo("Saved", f"Visualization saved to {file_path}")

        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def on_tab_close(self):
        """Clean up resources when tab is closed"""
        self.close_connection()
        plt.close(self.fig)

def create_analytics_tab(notebook, main_app):
    """
    Create the data analytics tab for the notebook.

    Args:
        notebook: The parent notebook widget
        main_app: The main application instance

    Returns:
        The created tab instance
    """
    tab_instance = SQLAnalyticsTab(notebook, main_app)

    # Add the tab to the notebook
    notebook.add(tab_instance.tab, text="Data Analytics")

    return tab_instance
