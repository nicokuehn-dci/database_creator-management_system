#!/usr/bin/env python3
"""
Test script to verify the modular database creator package works.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the modular package
from database_creator import DatabaseManager, DatabaseTemplates
# Templates are tested elsewhere
# # Templates are tested elsewhere
# from database_creator.templates import get_default_templates
from database_creator.advanced_templates import get_advanced_ecommerce_template

def test_package():
    """Test the basic functionality of the modular package."""
    print("Testing database creator package...")

    # Create temporary database
    db_path = "test_db.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    try:
        # Create a database manager
        db_manager = DatabaseManager(db_path)
        print(f"✓ Created database manager for {db_path}")

        # Load templates
        templates = DatabaseTemplates()
        templates.templates["advanced_ecommerce"] = \
                                                    get_advanced_ecommerce_template()
        print(f"✓ Loaded templates: {', '.join(templates.templates.keys())}")

        # Apply a template
        template_name = "web_store"
        if template_name in templates.templates:
            success = templates.apply_template(db_manager, template_name)
            if success:
                print(f"✓ Applied template '{template_name}'")
            else:
                print(f"✗ Failed to apply template '{template_name}'")
        else:
            print(f"✗ Template '{template_name}' not found")

        # Create a custom table
        table_name = "test_table"
        columns = ["id INTEGER PRIMARY KEY", "name TEXT", "value INTEGER"]
        success = db_manager.create_table(table_name, columns)
        if success:
            print(f"✓ Created table '{table_name}'")
        else:
            print(f"✗ Failed to create table '{table_name}'")

        # Insert data
        data = {"name": "Test Item", "value": 42}
        success = db_manager.insert_into_table(table_name, data)
        if success:
            print(f"✓ Inserted data into '{table_name}'")
        else:
            print(f"✗ Failed to insert data into '{table_name}'")

        # Query data
        results = db_manager.execute_query(f"SELECT * FROM {table_name}")
        if results:
            print(f"✓ Query returned {len(results)} rows")
            print(f"  First row: {results[0]}")
        else:
            print("✗ Query returned no results")

        print("\nAll tests completed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_package()
