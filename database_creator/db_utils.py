"""
Database utility functions for working with databases.
"""
import os
import sqlite3
import datetime
from tkinter import messagebox

from .db_connections import DatabaseConnection

class DatabaseUtils:
    """Utility functions for working with databases"""

    @staticmethod
    def get_db_stats(db_path):
        """Get statistics about a SQLite database.

        Args:
            db_path: Path to the database

        Returns:
            Dictionary with database stats (size, created, modified, tables, records)
        """
        stats = {
            'size': 0,
            'created': None,
            'modified': None,
            'tables': 0,
            'records': 0
        }

        try:
            # File size and dates
            stats['size'] = os.path.getsize(db_path)
            stats['created'] = datetime.datetime.fromtimestamp(os.path.getctime(db_path))
            stats['modified'] = datetime.datetime.fromtimestamp(os.path.getmtime(db_path))

            # Connect to the database
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()

                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                stats['tables'] = len(tables)

                # Count records in all tables
                total_records = 0
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    total_records += cursor.fetchone()[0]

                stats['records'] = total_records

                conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get database stats: {str(e)}")

        return stats

    @staticmethod
    def get_tables_from_sqlite_db(db_path):
        """Get list of tables from a SQLite database.

        Args:
            db_path: Path to the database

        Returns:
            List of table names
        """
        tables = []
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0] for table in cursor.fetchall()]
                conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to get tables: {str(e)}")

        return tables

    @staticmethod
    def get_table_schema(db_path, table_name):
        """Get schema information for a table.

        Args:
            db_path: Path to the database
            table_name: Name of the table

        Returns:
            List of column information (name, type, notnull, dflt_value, pk)
        """
        schema = []
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name});")
                schema = cursor.fetchall()
                conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to get table schema: {str(e)}")

        return schema

    @staticmethod
    def get_table_data(db_path, table_name, limit=100):
        """Get data from a table.

        Args:
            db_path: Path to the database
            table_name: Name of the table
            limit: Maximum number of rows to return (default: 100)

        Returns:
            Tuple of (columns, data) where columns is a list of column names
            and data is a list of rows
        """
        columns = []
        data = []

        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()

                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [column[1] for column in cursor.fetchall()]

                # Get data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
                data = cursor.fetchall()

                conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to get table data: {str(e)}")

        return columns, data

    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            String with formatted size (e.g., "1.23 MB")
        """
        # Define size units
        units = ['B', 'KB', 'MB', 'GB', 'TB']

        # Calculate the appropriate unit
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1

        # Format the size with 2 decimal places
        return f"{size_bytes:.2f} {units[i]}"

    @staticmethod
    def run_sql_query(db_path, query):
        """Run a SQL query on a SQLite database.

        Args:
            db_path: Path to the database
            query: SQL query to run

        Returns:
            Tuple of (success, result, error) where result contains columns and rows
            if successful, or error message if failed
        """
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()
                cursor.execute(query)

                # If it's a SELECT query, fetch results
                if query.strip().upper().startswith("SELECT"):
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]

                    # Get rows
                    rows = cursor.fetchall()

                    conn.close()
                    return True, {"columns": columns, "rows": rows}, None
                else:
                    # For non-SELECT queries, commit changes
                    conn.commit()
                    conn.close()
                    return True, {"message": "Query executed successfully"}, None

            return False, None, "Failed to connect to database"

        except sqlite3.Error as e:
            return False, None, str(e)
