"""
Database import and export functionality.
"""
import os
import csv
import json
import datetime
import sqlite3
from tkinter import messagebox

from .db_connections import DatabaseConnection


class DatabaseImportExport:
    """Class for handling database import and export functionality"""
    
    @staticmethod
    def export_table_data(db_path, table_name, export_format, file_path):
        """Export table data to a file.
        
        Args:
            db_path: Path to the database
            table_name: Name of the table
            export_format: Format to export (csv, json, sql)
            file_path: Path to save the file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = DatabaseConnection.connect_sqlite(db_path)
            if conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name};")
                data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                
                row_count = len(data)
                
                # Export based on format
                if export_format == "csv":
                    DatabaseImportExport._export_as_csv(file_path, columns, data)
                elif export_format == "json":
                    DatabaseImportExport._export_as_json(file_path, columns, data)
                elif export_format == "sql":
                    DatabaseImportExport._export_as_sql(
                        file_path, table_name, columns, data
                    )
                else:
                    return False, f"Unsupported export format: {export_format}"
                
                return True, f"Exported {row_count} rows to {os.path.basename(file_path)}"
            
            return False, "Failed to connect to database"
        
        except Exception as e:
            return False, f"Export error: {str(e)}"
    
    @staticmethod
    def _export_as_csv(file_path, columns, data):
        """Export data as CSV file.
        
        Args:
            file_path: Path to save the file
            columns: List of column names
            data: List of data rows
        """
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow(columns)
            
            # Write data rows
            for row in data:
                writer.writerow(row)
    
    @staticmethod
    def _export_as_json(file_path, columns, data):
        """Export data as JSON file.
        
        Args:
            file_path: Path to save the file
            columns: List of column names
            data: List of data rows
        """
        # Convert to list of dictionaries
        json_data = []
        for row in data:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            json_data.append(row_dict)
            
        # Write to file
        with open(file_path, "w") as f:
            json.dump(json_data, f, indent=2)
    
    @staticmethod
    def _export_as_sql(file_path, table_name, columns, data):
        """Export data as SQL insert statements.
        
        Args:
            file_path: Path to save the file
            table_name: Name of the table
            columns: List of column names
            data: List of data rows
        """
        with open(file_path, "w") as f:
            # Write header comment
            f.write(f"-- SQL dump for table {table_name}\n")
            f.write(f"-- Exported on {datetime.datetime.now()}\n\n")
            
            # Write column names
            cols = ", ".join(columns)
            
            # Write INSERT statements for each row
            for row in data:
                # Format values
                values = []
                for value in row:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, (int, float)):
                        values.append(str(value))
                    else:
                        # Escape single quotes in strings
                        values.append(f"'{str(value).replace('\'', '\'\'')}'")\
                
                value_str = ", ".join(values)
                f.write(f"INSERT INTO {table_name} ({cols}) VALUES ({value_str});\n")
    
    @staticmethod
    def import_csv_to_database(db_path, file_path, table_name=None):
        """Import data from a CSV file to a database.
        
        Args:
            db_path: Path to the database
            file_path: Path to the CSV file
            table_name: Optional name for the table, defaults to CSV filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # If table name not provided, use the CSV filename
            if not table_name:
                table_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Sanitize table name (remove non-alphanumeric characters)
                table_name = ''.join(
                    c if c.isalnum() else '_' for c in table_name
                )
            
            # Read CSV data
            with open(file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)  # First row as headers
                data = list(reader)
            
            # Connect to database
            conn = DatabaseConnection.connect_sqlite(db_path)
            if not conn:
                return False, "Failed to connect to database"
                
            cursor = conn.cursor()
            
            # Create table
            header_defs = []
            for header in headers:
                # Sanitize column name
                clean_header = ''.join(c if c.isalnum() else '_' for c in header)
                header_defs.append(f"{clean_header} TEXT")
            
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            create_stmt += ", ".join(header_defs)
            create_stmt += ")"
            
            cursor.execute(create_stmt)
            
            # Insert data
            for row in data:
                # Ensure row has the right number of columns
                if len(row) == len(headers):
                    placeholders = ", ".join(["?"] * len(headers))
                    cursor.execute(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        row
                    )
            
            conn.commit()
            conn.close()
            
            return True, f"Imported {len(data)} rows into table '{table_name}'"
            
        except Exception as e:
            return False, f"Import error: {str(e)}"
    
    @staticmethod
    def import_excel_to_database(db_path, file_path, sheet_name=None):
        """Import data from an Excel file to a database.
        
        Args:
            db_path: Path to the database
            file_path: Path to the Excel file
            sheet_name: Optional sheet name, defaults to first sheet
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if openpyxl is installed
            try:
                import openpyxl
            except ImportError:
                return False, (
                    "Missing dependency: openpyxl. "
                    "Please install it with 'pip install openpyxl'"
                )
                
            # Load the Excel workbook
            workbook = openpyxl.load_workbook(file_path, read_only=True)
            
            # Get the sheet
            if sheet_name and sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
            else:
                sheet = workbook.active
                
            table_name = sheet.title
            
            # Sanitize table name
            table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
            
            # Connect to database
            conn = DatabaseConnection.connect_sqlite(db_path)
            if not conn:
                return False, "Failed to connect to database"
                
            cursor = conn.cursor()
            
            # Get headers from first row
            rows = list(sheet.rows)
            if not rows:
                return False, "No data found in Excel sheet"
                
            headers = [cell.value for cell in rows[0]]
            
            # Create table
            clean_headers = []
            for header in headers:
                if header is None:
                    header = "Column"
                # Sanitize column name
                clean_header = ''.join(c if c.isalnum() else '_' for c in str(header))
                clean_headers.append(clean_header)
            
            create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            create_stmt += ", ".join([f"{header} TEXT" for header in clean_headers])
            create_stmt += ")"
            
            cursor.execute(create_stmt)
            
            # Insert data from remaining rows
            row_count = 0
            for row in rows[1:]:  # Skip header row
                values = [cell.value if cell.value is not None else "" for cell in row]
                if len(values) == len(headers):
                    placeholders = ", ".join(["?"] * len(values))
                    cursor.execute(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        values
                    )
                    row_count += 1
            
            conn.commit()
            conn.close()
            
            return True, f"Imported {row_count} rows into table '{table_name}'"
            
        except Exception as e:
            return False, f"Import error: {str(e)}"
