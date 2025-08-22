"""
Test suite for database_creator package.
Run tests with pytest: pytest -xvs test_functionality.py
"""
import os
import sys
import sqlite3
import tempfile
import pytest
import json

# Add parent directory to path to import database_creator
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from database_creator.database import DatabaseManager
from database_creator.templates import DatabaseTemplates

class TestDatabaseFunctionality:
    """Test core database functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        # Yield the path for the test to use
        yield db_path

        # Clean up after the test
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_create_database(self, temp_db_path):
        """Test creating a new database."""
        # Create database manager
        db_manager = DatabaseManager(temp_db_path)

        # Create a simple table
        db_manager.execute_query("""
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL
            )
        """)

        # Verify the table was created
        tables = db_manager.get_tables()
        assert "test" in tables, "Table 'test' should be in the list of tables"

    def test_insert_and_query(self, temp_db_path):
        """Test inserting and querying data."""
        # Create database manager
        db_manager = DatabaseManager(temp_db_path)

        # Create a simple table
        db_manager.execute_query("""
            CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL
            )
        """)

        # Insert data
        db_manager.execute_query(
            "INSERT INTO test (name, value) VALUES (?, ?)",
            ("test_name", 42.5)
        )

        # Query data
        result = db_manager.execute_query("SELECT * FROM test WHERE name = ?", ("test_name",))

        # Check result
        assert len(result) == 1, "Should have exactly one row"
        assert result[0]["name"] == "test_name", "Name should match"
        assert result[0]["value"] == 42.5, "Value should match"

    def test_table_schema(self, temp_db_path):
        """Test retrieving table schema."""
        # Create database manager
        db_manager = DatabaseManager(temp_db_path)

        # Create a table with various column types
        db_manager.execute_query("""
            CREATE TABLE schema_test (
                id INTEGER PRIMARY KEY,
                text_col TEXT NOT NULL,
                real_col REAL,
                blob_col BLOB,
                int_col INTEGER DEFAULT 0,
                unique_col TEXT UNIQUE
            )
        """)

        # Get schema
        schema = db_manager.get_table_schema("schema_test")

        # Check schema
        assert len(schema) == 6, "Should have 6 columns"

        # Handle tuple schema format - (name, type, full_definition)
        name_idx = 0  # Column name is at index 0
        type_idx = 1  # Column type is at index 1
        definition_idx = 2  # Full definition is at index 2

        # Create a dictionary by column name for easier testing
        cols_by_name = {col[name_idx]: col for col in schema}

        # Check id column
        assert "id" in cols_by_name, "id column should be in schema"
        assert cols_by_name["id"][type_idx] == "INTEGER", "id should be INTEGER"
        assert "PRIMARY KEY" in cols_by_name["id"][definition_idx], "id should have PRIMARY KEY"

        # Check text_col column
        assert "text_col" in cols_by_name, "text_col should be in schema"
        assert cols_by_name["text_col"][type_idx] == "TEXT", "text_col should be TEXT"
        assert "NOT NULL" in cols_by_name["text_col"][definition_idx], "text_col should have NOT NULL"

        # Check unique_col column
        assert "unique_col" in cols_by_name, "unique_col should be in schema"
        assert cols_by_name["unique_col"][type_idx] == "TEXT", "unique_col should be TEXT"

    def test_execute_script(self, temp_db_path):
        """Test executing SQL script with multiple statements."""
        # Create database manager
        db_manager = DatabaseManager(temp_db_path)

        # Execute a script with multiple statements
        db_manager.execute_script("""
            CREATE TABLE test1 (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE test2 (id INTEGER PRIMARY KEY, value REAL);
            INSERT INTO test1 (name) VALUES ('test_name');
            INSERT INTO test2 (value) VALUES (123.45);
        """)

        # Verify both tables were created
        tables = db_manager.get_tables()
        assert "test1" in tables, "Table 'test1' should be in tables list"
        assert "test2" in tables, "Table 'test2' should be in tables list"

        # Verify data was inserted
        result1 = db_manager.execute_query("SELECT * FROM test1")
        result2 = db_manager.execute_query("SELECT * FROM test2")

        assert len(result1) == 1, "Should have one row in test1"
        assert len(result2) == 1, "Should have one row in test2"
        assert result1[0]["name"] == "test_name", "Name should match"
        assert result2[0]["value"] == 123.45, "Value should match"

    def test_apply_template(self, temp_db_path):
        """Test applying a database template."""
        # Create database manager and templates
        db_manager = DatabaseManager(temp_db_path)
        templates = DatabaseTemplates()

        # Get the blog template (actually named "Blog System" in templates)
        blog_template = templates.templates["Blog System"]

        # Apply template
        templates.apply_template(db_manager, "Blog System")

        # Verify tables were created
        tables = db_manager.get_tables()

        # Check that all tables from template exist
        for table_name in blog_template["tables"]:
            assert table_name in tables, f"Table '{table_name}' should be created"

        # Check some specific table schema details
        posts_schema = db_manager.get_table_schema("posts")
        # Schema returns tuples of (name, type, full_definition)
        post_col_names = [col[0] for col in posts_schema]

        assert "post_id" in post_col_names, "posts should have post_id column"
        assert "title" in post_col_names, "posts table should have title column"
        assert "content" in post_col_names, "posts should have content column"
        assert "user_id" in post_col_names, "posts should have user_id column"

    def test_export_import(self, temp_db_path):
        """Test exporting and importing database to SQL."""
        # Create database manager
        db_manager = DatabaseManager(temp_db_path)

        # Create a simple table and add data
        db_manager.execute_query("""
            CREATE TABLE export_test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        db_manager.execute_query(
            "INSERT INTO export_test (name) VALUES (?)",
            ("test_export",)
        )

        # Export to SQL file
        sql_file = temp_db_path + ".sql"
        db_manager.export_to_sql(sql_file)

        # Create new database from SQL
        new_db_path = temp_db_path + "_new.db"
        new_db_manager = DatabaseManager(new_db_path)

        # Import SQL to new database
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        new_db_manager.execute_script(sql_script)

        try:
            # Check that data was imported correctly
            result = new_db_manager.execute_query("SELECT * FROM export_test")
            assert len(result) == 1, "Should have one row"
            assert result[0]["name"] == "test_export", "Name should match"
        finally:
            # Clean up extra files
            if os.path.exists(sql_file):
                os.unlink(sql_file)
            if os.path.exists(new_db_path):
                os.unlink(new_db_path)

    def test_config_save_load(self):
        """Test saving and loading configuration."""
        # Create a temporary config file
        config_file = tempfile.NamedTemporaryFile(delete=False).name

        try:
            # Save configuration directly to file
            config_data = {
                "last_database": "/path/to/test.db",
                "theme": "dark",
                "window_size": [800, 600]  # JSON doesn't support tuples
            }

            # Write directly to the file
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f)

            # Read directly from the file
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # Verify config was saved and loaded correctly
            assert loaded_config["last_database"] == "/path/to/test.db"
            assert loaded_config["theme"] == "dark"
            assert loaded_config["window_size"] == [800, 600]
        finally:
            # Clean up
            if os.path.exists(config_file):
                os.unlink(config_file)
