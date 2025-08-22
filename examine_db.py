import sqlite3
import os
import sys

def examine_database(db_path):
    """Examine database structure and print tables and schema."""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist.")
        return

    print(f"\n--- Examining database: {db_path} ---")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            conn.close()
            return
            
        print(f"Tables found: {', '.join([t[0] for t in tables])}")
        
        # For each table, get its schema and sample data
        for table in tables:
            table_name = table[0]
            print(f"\n## Table: {table_name}")
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            schema = cursor.fetchall()
            
            if schema:
                print("Schema:")
                for col in schema:
                    print(f"  {col[1]} ({col[2]})", end="")
                    if col[3]:  # NOT NULL constraint
                        print(" NOT NULL", end="")
                    if col[5]:  # PRIMARY KEY
                        print(" PRIMARY KEY", end="")
                    print()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Get sample data (up to 5 rows)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                
                if rows:
                    print("Sample data:")
                    # Get column names for better output
                    column_names = [desc[0] for desc in cursor.description]
                    print(f"  {column_names}")
                    
                    for row in rows:
                        print(f"  {row}")
        
        conn.close()
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

if __name__ == "__main__":
    # Check if database path is provided as argument
    if len(sys.argv) > 1:
        examine_database(sys.argv[1])
    else:
        # Examine all databases in the project
        print("Examining all databases in the project...")
        
        # Root database
        if os.path.exists("database.db"):
            examine_database("database.db")
        
        # Sample databases
        sample_dir = "sample_databases"
        if os.path.exists(sample_dir):
            for file in os.listdir(sample_dir):
                if file.endswith(".db"):
                    examine_database(os.path.join(sample_dir, file))
        
        # Databases folder
        databases_dir = "databases"
        if os.path.exists(databases_dir):
            for file in os.listdir(databases_dir):
                if file.endswith(".db"):
                    examine_database(os.path.join(databases_dir, file))
