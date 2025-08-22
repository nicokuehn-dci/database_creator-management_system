"""
Core database functionality: connection handling and database management.
"""

import sqlite3
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from .config import load_config, save_config, DEFAULT_DB_NAME, DB_STORAGE_DIR

# Database connection with context manager support
class DatabaseConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

# Database manager class
class DatabaseManager:
    def __init__(self, db_path: str = DEFAULT_DB_NAME):
        """Initialize the database manager with a path to the SQLite file."""
        # If the path is not absolute and doesn't exist in the current directory, use storage dir
        if not os.path.isabs(db_path):
            # Check if it's in the database storage directory
            storage_path = os.path.join(DB_STORAGE_DIR, os.path.basename(db_path))
            if os.path.exists(storage_path):
                self.db_path = storage_path
            elif not os.path.exists(db_path):
                # Create a new database in the storage directory
                self.db_path = storage_path
            else:
                # Keep original path if it exists in the current directory
                self.db_path = db_path
        else:
            self.db_path = db_path

        self.config = load_config()

        # Add to recent databases (store relative path if in DB_STORAGE_DIR)
        if self.db_path.startswith(DB_STORAGE_DIR):
            # Store relative path for databases in the storage directory
            relative_path = os.path.relpath(self.db_path, DB_STORAGE_DIR)
            db_for_config = relative_path
        else:
            # Store absolute path for databases outside storage directory
            db_for_config = self.db_path

        if "recent_databases" in self.config and db_for_config not in self.config["recent_databases"]:
            self.config["recent_databases"].insert(0, db_for_config)
            self.config["recent_databases"] = self.config["recent_databases"][:self.config.get("max_recent", 5)]
            save_config(self.config)

    def close(self):
        """Close any open resources."""
        pass  # No persistent connections to close

    def execute_script(self, sql_script: str) -> bool:
        """Execute a SQL script with multiple statements."""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executescript(sql_script)
            return True
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return False

    def execute_query(self, query: str, parameters: tuple = ()) -> List[Dict]:
        """Execute a SQL query and return results as a list of dictionaries."""
        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, parameters)

                # Get results if available
                query_upper = query.strip().upper()
                if (query_upper.startswith("SELECT") or
                    query_upper.startswith("PRAGMA") or
                    query_upper.find(" FROM ") > 0):
                    try:
                        rows = cursor.fetchall()
                        if rows:
                            # Check if Row objects with dictionary access
                            if hasattr(rows[0], 'keys'):
                                return [dict(row) for row in rows]
                            # Return list of dicts with column indexes as keys
                            else:
                                cols = [desc[0] for desc in cursor.description]
                                return [dict(zip(cols, row)) for row in rows]
                        return []
                    except Exception as fetch_err:
                        print(f"Warning: Error fetching results: {fetch_err}")

                # For other queries (INSERT, UPDATE, DELETE)
                last_id = cursor.lastrowid
                return [{"rowcount": cursor.rowcount, "last_insert_rowid()": last_id}]
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return []

    def create_table(self, table_name: str, columns, constraints=None) -> bool:
        """
        Create a table with the given name and columns.

        Args:
            table_name: Name of the table
            columns: Either a dictionary mapping column names to definitions
                     or a list of column definitions
            constraints: List of table-level constraints
        """
        try:
            column_defs = []

            # Handle different input formats
            if isinstance(columns, dict):
                # Dictionary format: {'col_name': 'type constraints'}
                for col_name, col_def in columns.items():
                    column_defs.append(f"{col_name} {col_def}")
            elif isinstance(columns, list):
                # List format: ['col_name type constraints']
                column_defs = columns
            else:
                raise ValueError(
                    "columns must be a dictionary or list of column definitions"
                )

            # Add any additional constraints
            if constraints:
                column_defs.extend(constraints)

            create_stmt = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(column_defs)}
            );
            """

            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(create_stmt)
            return True
        except sqlite3.Error as e:
            print(f"❌ Could not create table {table_name}: {e}")
            return False

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?;
        """
        result = self.execute_query(query, (table_name,))
        return len(result) > 0

    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get information about a table's columns."""
        if not self.table_exists(table_name):
            return []

        return self.execute_query(f"PRAGMA table_info({table_name});")

    def export_database(self, format_type: str, output_path: str) -> bool:
        """Export the database to the specified format."""
        try:
            if format_type == 'sql':
                return self._export_to_sql(output_path)
            elif format_type == 'json':
                return self._export_to_json(output_path)
            elif format_type == 'csv':
                return self._export_to_csv_dir(output_path)
            else:
                print(f"❌ Unsupported export format: {format_type}")
                return False
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False

    def _export_to_sql(self, output_path: str) -> bool:
        """Export database to SQL statements."""
        try:
            with DatabaseConnection(self.db_path) as conn:
                with open(output_path, 'w') as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\n")
            return True
        except Exception as e:
            print(f"❌ SQL export error: {e}")
            return False

    def _export_to_json(self, output_path: str) -> bool:
        """Export database tables to JSON."""
        try:
            # Get all table names
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )

            data = {}
            for table in tables:
                table_name = table['name']
                rows = self.execute_query(f"SELECT * FROM {table_name};")
                data[table_name] = rows

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"❌ JSON export error: {e}")
            return False

    def _export_to_csv_dir(self, output_dir: str) -> bool:
        """Export each table to a separate CSV file in the given directory."""
        try:
            import csv
            os.makedirs(output_dir, exist_ok=True)

            # Get all table names
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )

            for table in tables:
                table_name = table['name']
                rows = self.execute_query(f"SELECT * FROM {table_name};")

                if not rows:
                    continue

                output_file = os.path.join(output_dir, f"{table_name}.csv")
                with open(output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)

            return True
        except Exception as e:
            print(f"❌ CSV export error: {e}")
            return False

    def import_from_sql(self, sql_file: str) -> bool:
        """Import database from SQL file."""
        try:
            with open(sql_file, 'r') as f:
                sql_script = f.read()

            return self.execute_script(sql_script)
        except Exception as e:
            print(f"❌ Import error: {e}")
            return False

    def import_from_json(self, json_file: str) -> bool:
        """Import database from JSON file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()

                for table_name, rows in data.items():
                    if not rows:
                        continue

                    # Create table with columns from the first row
                    columns = list(rows[0].keys())
                    placeholders = ', '.join(['?'] * len(columns))

                    # Create table
                    col_defs = [f"{col} TEXT" for col in columns]
                    create_stmt = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {', '.join(col_defs)}
                    );
                    """
                    cursor.execute(create_stmt)

                    # Insert data
                    insert_stmt = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"

                    for row in rows:
                        values = [row[col] for col in columns]
                        cursor.execute(insert_stmt, values)

            return True
        except Exception as e:
            print(f"❌ JSON import error: {e}")
            return False

    def get_tables(self) -> List[str]:
        """Get all table names in the database."""
        query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
        results = self.execute_query(query)
        return [row['name'] for row in results]

    def get_table_schema(self, table_name: str) -> List[tuple]:
        """Get the schema of a table as a list of column tuples."""
        if not self.table_exists(table_name):
            return []

        result = []
        # Get column information - should now return proper dictionaries
        columns = self.execute_query(f"PRAGMA table_info({table_name});")

        for col in columns:
            name = col.get('name', 'unknown')
            col_type = col.get('type', 'TEXT')
            pk = int(col.get('pk', 0))
            notnull = int(col.get('notnull', 0))
            dflt_value = col.get('dflt_value', None)

            # Format as "name type constraints"
            column_def = f"{name} {col_type}"

            if pk == 1:
                column_def += " PRIMARY KEY"
            if notnull == 1:
                column_def += " NOT NULL"
            if dflt_value is not None:
                column_def += f" DEFAULT {dflt_value}"

            # Add column definition tuple (name, type, full_definition)
            result.append((name, col_type, column_def))

        return result

    def insert_into_table(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Insert data into a table."""
        if not data:
            return False

        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?'] * len(columns))

        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({placeholders});
        """

        try:
            with DatabaseConnection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
            return True
        except sqlite3.Error as e:
            print(f"❌ Insert error: {e}")
            return False

    def export_to_sql(self, output_path: str) -> bool:
        """Export database to SQL statements (alias for _export_to_sql)."""
        return self._export_to_sql(output_path)
