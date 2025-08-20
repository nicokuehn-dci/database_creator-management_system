"""
Database connections and operations module.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import threading
import datetime

from ..config import DB_STORAGE_DIR, ensure_directory_exists, load_config, save_config


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
        return f"{size_bytes:.2f} TB"
    
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
