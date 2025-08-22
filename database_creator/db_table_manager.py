"""
Database table management module for handling table operations.
"""
import os
import sqlite3
import json
import datetime
from tkinter import messagebox

from .db_connections import DatabaseConnection

class DatabaseTableManager:
    """Class for managing database table operations"""

    @staticmethod
    def add_row(db_path, table_name, columns, values):
        """Add a new row to a table.

        Args:
            db_path: Path to the database
            table_name: Name of the table
            columns: List of column names
            values: List of values to insert

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()

                # Create SQL query
                placeholders = ", ".join(["?"] * len(columns))
                cols = ", ".join(columns)

                cursor.execute(
                    f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})",
                    values
                )

                conn.commit()
                conn.close()
                return True
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to add row: {str(e)}")
            return False

    @staticmethod
    def update_row(db_path, table_name, columns, old_values, new_values):
        """Update an existing row in a table.

        Args:
            db_path: Path to the database
            table_name: Name of the table
            columns: List of column names
            old_values: List of current values (to identify the row)
            new_values: List of new values to set

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()

                # Create SET part of query
                set_parts = [f"{col} = ?" for col in columns]
                set_clause = ", ".join(set_parts)

                # Create WHERE clause to identify the exact row
                where_parts = []
                params = []

                for i, col in enumerate(columns):
                    if old_values[i] is None or old_values[i] == "":
                        where_parts.append(f"{col} IS NULL")
                    else:
                        where_parts.append(f"{col} = ?")
                        params.append(old_values[i])

                where_clause = " AND ".join(where_parts)

                # Execute update query
                cursor.execute(
                    f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}",
                    new_values + params
                )

                conn.commit()
                conn.close()
                return True
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to update row: {str(e)}")
            return False

    @staticmethod
    def delete_row(db_path, table_name, columns, values):
        """Delete a row from a table.

        Args:
            db_path: Path to the database
            table_name: Name of the table
            columns: List of column names
            values: List of values to identify the row

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()

                # Create WHERE clause with all columns for precise matching
                where_parts = []
                params = []

                for i, col in enumerate(columns):
                    if values[i] is None or values[i] == "":
                        where_parts.append(f"{col} IS NULL")
                    else:
                        where_parts.append(f"{col} = ?")
                        params.append(values[i])

                where_clause = " AND ".join(where_parts)

                # Execute delete query
                cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}", params)

                conn.commit()
                conn.close()
                return True
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to delete row: {str(e)}")
            return False
