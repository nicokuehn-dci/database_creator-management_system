"""
Database connection utilities for working with SQLite and external databases.
"""
import os
import sqlite3
import json
import threading
from tkinter import messagebox, ttk
import tkinter as tk

from .config import DB_STORAGE_DIR, load_config, save_config

class DatabaseConnection:
    """Class for handling database connections"""

    @staticmethod
    def connect_sqlite(db_path):
        """Connect to a SQLite database

        Args:
            db_path: Path to the SQLite database

        Returns:
            SQLite connection object or None if connection failed
        """
        try:
            conn = sqlite3.connect(db_path)
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not connect to database: {str(e)}")
            return None

    @staticmethod
    def connect_external(db_type, conn_info):
        """Connect to an external database system

        Args:
            db_type: Type of database (mysql, postgresql, etc.)
            conn_info: Dictionary with connection parameters

        Returns:
            Database connection object or None if connection failed
        """
        try:
            if db_type == "mysql":
                import pymysql
                conn = pymysql.connect(
                    host=conn_info.get("host", "localhost"),
                    user=conn_info.get("user", ""),
                    password=conn_info.get("password", ""),
                    database=conn_info.get("database", ""),
                    port=conn_info.get("port", 3306)
                )
                return conn
            elif db_type == "postgresql":
                import psycopg2
                conn = psycopg2.connect(
                    host=conn_info.get("host", "localhost"),
                    user=conn_info.get("user", ""),
                    password=conn_info.get("password", ""),
                    dbname=conn_info.get("database", ""),
                    port=conn_info.get("port", 5432)
                )
                return conn
            elif db_type == "sqlserver":
                import pyodbc
                conn_str = (
                    f"DRIVER={{SQL Server}};"
                    f"SERVER={conn_info.get('host', 'localhost')};"
                    f"DATABASE={conn_info.get('database', '')};"
                    f"UID={conn_info.get('user', '')};"
                    f"PWD={conn_info.get('password', '')};"
                )
                conn = pyodbc.connect(conn_str)
                return conn
            elif db_type == "oracle":
                import cx_Oracle
                conn = cx_Oracle.connect(
                    f"{conn_info.get('user', '')}/{conn_info.get('password', '')}"
                    f"@{conn_info.get('host', 'localhost')}:"
                    f"{conn_info.get('port', 1521)}/"
                    f"{conn_info.get('database', '')}"
                )
                return conn
            else:
                messagebox.showerror(
                    "Connection Error",
                    f"Unsupported database type: {db_type}"
                )
                return None
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            return None

    @staticmethod
    def save_external_connection(name, db_type, conn_info):
        """Save external connection information to config

        Args:
            name: Connection name
            db_type: Database type (mysql, postgresql, etc.)
            conn_info: Connection parameters dictionary
        """
        config = load_config()

        if "external_connections" not in config:
            config["external_connections"] = {}

        # Store connection info
        conn_info["type"] = db_type
        config["external_connections"][name] = conn_info

        # Save updated config
        save_config(config)

    @staticmethod
    def remove_external_connection(name):
        """Remove an external connection from config

        Args:
            name: Connection name to remove
        """
        config = load_config()

        if "external_connections" in config and name in config["external_connections"]:
            del config["external_connections"][name]
            save_config(config)

    @staticmethod
    def get_external_connections():
        """Get all external connections from config

        Returns:
            Dictionary of external connections
        """
        config = load_config()
        return config.get("external_connections", {})

    @staticmethod
    def test_connection(db_type, conn_info, progress_callback=None):
        """Test a connection to an external database

        Args:
            db_type: Database type (mysql, postgresql, etc.)
            conn_info: Connection parameters dictionary
            progress_callback: Optional callback function for progress updates

        Returns:
            Tuple of (success, message)
        """
        try:
            # Update progress if callback provided
            if progress_callback:
                progress_callback("Connecting...")

            # Try to establish connection based on database type
            if db_type == "mysql":
                import pymysql
                conn = pymysql.connect(
                    host=conn_info.get("host", "localhost"),
                    user=conn_info.get("user", ""),
                    password=conn_info.get("password", ""),
                    database=conn_info.get("database", ""),
                    port=int(conn_info.get("port", 3306)),
                    connect_timeout=5
                )

                # Test querying database info
                if progress_callback:
                    progress_callback("Testing connection...")

                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                return True, f"Successfully connected to MySQL: {version}"

            elif db_type == "postgresql":
                import psycopg2
                conn = psycopg2.connect(
                    host=conn_info.get("host", "localhost"),
                    user=conn_info.get("user", ""),
                    password=conn_info.get("password", ""),
                    dbname=conn_info.get("database", ""),
                    port=int(conn_info.get("port", 5432)),
                    connect_timeout=5
                )

                # Test querying database info
                if progress_callback:
                    progress_callback("Testing connection...")

                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                return True, f"Successfully connected to PostgreSQL: {version}"

            elif db_type == "sqlserver":
                import pyodbc
                conn_str = (
                    f"DRIVER={{SQL Server}};"
                    f"SERVER={conn_info.get('host', 'localhost')};"
                    f"DATABASE={conn_info.get('database', '')};"
                    f"UID={conn_info.get('user', '')};"
                    f"PWD={conn_info.get('password', '')};"
                    f"Connection Timeout=5;"
                )
                conn = pyodbc.connect(conn_str)

                # Test querying database info
                if progress_callback:
                    progress_callback("Testing connection...")

                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                return True, f"Successfully connected to SQL Server: {version}"

            elif db_type == "oracle":
                import cx_Oracle
                conn = cx_Oracle.connect(
                    f"{conn_info.get('user', '')}/{conn_info.get('password', '')}"
                    f"@{conn_info.get('host', 'localhost')}:"
                    f"{conn_info.get('port', 1521)}/"
                    f"{conn_info.get('database', '')}",
                    encoding="UTF-8"
                )

                # Test querying database info
                if progress_callback:
                    progress_callback("Testing connection...")

                cursor = conn.cursor()
                cursor.execute("SELECT * FROM v$version")
                version = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                return True, f"Successfully connected to Oracle: {version}"

            else:
                return False, f"Unsupported database type: {db_type}"

        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    @staticmethod
    def show_connection_dialog(parent, on_success=None):
        """Show dialog to configure and test an external database connection

        Args:
            parent: Parent widget
            on_success: Callback function to call on successful connection
        """
        # Create connection dialog
        connection_dialog = tk.Toplevel(parent)
        connection_dialog.title("Connect to External Database")
        connection_dialog.geometry("500x400")
        connection_dialog.transient(parent)
        connection_dialog.grab_set()

        # Connection name
        ttk.Label(connection_dialog, text="Connection Name:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        name_entry = ttk.Entry(connection_dialog, width=30)
        name_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        # Database type
        ttk.Label(connection_dialog, text="Database Type:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        db_type_var = tk.StringVar(value="mysql")
        db_type_combo = ttk.Combobox(
            connection_dialog,
            textvariable=db_type_var,
            values=["mysql", "postgresql", "sqlserver", "oracle"],
            state="readonly",
            width=28
        )
        db_type_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # Host/Server
        ttk.Label(connection_dialog, text="Host:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        host_entry = ttk.Entry(connection_dialog, width=30)
        host_entry.insert(0, "localhost")
        host_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        # Port
        ttk.Label(connection_dialog, text="Port:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5
        )
        port_var = tk.StringVar(value="3306")
        port_entry = ttk.Entry(connection_dialog, textvariable=port_var, width=10)
        port_entry.grid(row=3, column=1, sticky="w", padx=10, pady=5)

        # Database name
        ttk.Label(connection_dialog, text="Database:").grid(
            row=4, column=0, sticky="w", padx=10, pady=5
        )
        database_entry = ttk.Entry(connection_dialog, width=30)
        database_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

        # Username
        ttk.Label(connection_dialog, text="Username:").grid(
            row=5, column=0, sticky="w", padx=10, pady=5
        )
        user_entry = ttk.Entry(connection_dialog, width=30)
        user_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)

        # Password
        ttk.Label(connection_dialog, text="Password:").grid(
            row=6, column=0, sticky="w", padx=10, pady=5
        )
        password_entry = ttk.Entry(connection_dialog, width=30, show="*")
        password_entry.grid(row=6, column=1, sticky="ew", padx=10, pady=5)

        # Additional options (in the future, could add SSL, timeout, etc.)
        ttk.Label(connection_dialog, text="Options:").grid(
            row=7, column=0, sticky="nw", padx=10, pady=5
        )
        options_frame = ttk.Frame(connection_dialog)
        options_frame.grid(row=7, column=1, sticky="ew", padx=10, pady=5)

        save_password_var = tk.BooleanVar(value=True)
        save_password_check = ttk.Checkbutton(
            options_frame,
            text="Save password",
            variable=save_password_var
        )
        save_password_check.pack(anchor="w")

        # Status/progress indicator
        status_var = tk.StringVar()
        status_label = ttk.Label(
            connection_dialog,
            textvariable=status_var,
            foreground="blue"
        )
        status_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        # Progress bar for connection testing
        progress = ttk.Progressbar(connection_dialog, mode='indeterminate')
        progress.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        # Update port when database type changes
        def update_port(*args):
            db_type = db_type_var.get()
            if db_type == "mysql":
                port_var.set("3306")
            elif db_type == "postgresql":
                port_var.set("5432")
            elif db_type == "sqlserver":
                port_var.set("1433")
            elif db_type == "oracle":
                port_var.set("1521")

        db_type_combo.bind("<<ComboboxSelected>>", update_port)

        # Test connection function
        def test_connection():
            # Get connection info
            db_type = db_type_var.get()
            conn_info = {
                "host": host_entry.get(),
                "port": port_entry.get(),
                "database": database_entry.get(),
                "user": user_entry.get(),
                "password": password_entry.get() if save_password_var.get() else ""
            }

            # Validate inputs
            if not name_entry.get().strip():
                status_var.set("Error: Connection name is required")
                return

            if not conn_info["host"]:
                status_var.set("Error: Host is required")
                return

            if not conn_info["database"]:
                status_var.set("Error: Database name is required")
                return

            # Show progress
            progress.start()
            status_var.set("Testing connection...")

            # Use a thread to avoid UI freeze during connection attempt
            def test_thread():
                success, message = DatabaseConnection.test_connection(
                    db_type,
                    conn_info,
                    lambda msg: status_var.set(msg)
                )

                # Update UI from main thread
                connection_dialog.after(0, lambda: handle_test_result(success, message))

            def handle_test_result(success, message):
                progress.stop()
                if success:
                    status_var.set(message)
                    # Enable the save button
                    save_button.config(state="normal")
                else:
                    status_var.set(message)

            # Start the test thread
            threading.Thread(target=test_thread, daemon=True).start()

        # Save connection function
        def save_connection():
            name = name_entry.get().strip()
            db_type = db_type_var.get()

            # Check if name is valid
            if not name:
                status_var.set("Error: Connection name is required")
                return

            # Collect connection info
            conn_info = {
                "host": host_entry.get(),
                "port": port_entry.get(),
                "database": database_entry.get(),
                "user": user_entry.get()
            }

            # Only save password if checkbox is checked
            if save_password_var.get():
                conn_info["password"] = password_entry.get()

            # Save to config
            DatabaseConnection.save_external_connection(name, db_type, conn_info)

            # Close dialog and notify caller
            if on_success:
                on_success(name, db_type)

            connection_dialog.destroy()

        # Button frame
        button_frame = ttk.Frame(connection_dialog)
        button_frame.grid(row=10, column=0, columnspan=2, sticky="e", padx=10, pady=10)

        # Test button
        test_button = ttk.Button(button_frame, text="Test Connection", command=test_connection)
        test_button.pack(side=tk.LEFT, padx=5)

        # Save button (disabled until connection tested successfully)
        save_button = ttk.Button(
            button_frame,
            text="Save Connection",
            command=save_connection,
            state="disabled"
        )
        save_button.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=connection_dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)

        # Configure grid weights
        connection_dialog.columnconfigure(1, weight=1)

        # Center the dialog on parent
        connection_dialog.update_idletasks()
        parent_x = parent.winfo_rootx() + (parent.winfo_width() // 2)
        parent_y = parent.winfo_rooty() + (parent.winfo_height() // 2)
        dialog_width = connection_dialog.winfo_width()
        dialog_height = connection_dialog.winfo_height()
        x = max(0, parent_x - (dialog_width // 2))
        y = max(0, parent_y - (dialog_height // 2))
        connection_dialog.geometry(f"+{x}+{y}")

class DatabaseUtils:
    """Utility functions for database operations"""

    @staticmethod
    def get_tables_from_sqlite_db(db_path):
        """Get table names from a SQLite database

        Args:
            db_path: Path to the SQLite database

        Returns:
            List of table names
        """
        conn = DatabaseConnection.connect_sqlite(db_path)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
                cursor.close()
                conn.close()
                return tables
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to get tables: {str(e)}")
                if conn:
                    conn.close()
                return []
        return []

    @staticmethod
    def get_table_schema(db_path, table_name):
        """Get schema for a table in a SQLite database

        Args:
            db_path: Path to the SQLite database
            table_name: Name of the table

        Returns:
            List of column definitions (name, type, etc.)
        """
        conn = DatabaseConnection.connect_sqlite(db_path)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name});")
                schema = cursor.fetchall()
                cursor.close()
                conn.close()
                return schema
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to get schema: {str(e)}")
                if conn:
                    conn.close()
                return []
        return []

    @staticmethod
    def get_table_data(db_path, table_name, limit=100):
        """Get data from a table in a SQLite database

        Args:
            db_path: Path to the SQLite database
            table_name: Name of the table
            limit: Maximum number of rows to return

        Returns:
            Tuple of (column_names, data_rows)
        """
        conn = DatabaseConnection.connect_sqlite(db_path)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
                data = cursor.fetchall()

                # Get column names
                column_names = [description[0] for description in cursor.description]

                cursor.close()
                conn.close()
                return column_names, data
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to get data: {str(e)}")
                if conn:
                    conn.close()
                return [], []
        return [], []

    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in bytes to human readable format

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"  # Just in case we ever have terabyte databases!

    @staticmethod
    def get_db_stats(db_path):
        """Get statistics for a SQLite database

        Args:
            db_path: Path to the SQLite database

        Returns:
            Dictionary with database statistics
        """
        stats = {
            'size': os.path.getsize(db_path) if os.path.exists(db_path) else 0,
            'tables': 0,
            'records': 0,
            'created': '',
            'modified': ''
        }

        # Get file timestamps
        if os.path.exists(db_path):
            stats['created'] = datetime.datetime.fromtimestamp(os.path.getctime(db_path))
            stats['modified'] = datetime.datetime.fromtimestamp(os.path.getmtime(db_path))

        # Get table count and record counts
        conn = DatabaseConnection.connect_sqlite(db_path)
        if conn:
            try:
                cursor = conn.cursor()

                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = [row[0] for row in cursor.fetchall()]
                stats['tables'] = len(tables)

                # Get record count for each table
                total_records = 0
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    total_records += count

                stats['records'] = total_records

                cursor.close()
                conn.close()
            except sqlite3.Error:
                if conn:
                    conn.close()

        return stats
