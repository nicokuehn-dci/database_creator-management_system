"""
Command Line Interface for the database creator application.
"""
import os
import sys
import argparse
from typing import Dict, Any, List, Optional, Tuple

from .database import DatabaseManager
from .config import load_config, save_config
from .templates import DatabaseTemplates
from .security import hash_password
from .advanced_templates import get_advanced_ecommerce_template


class CLI:
    """Command Line Interface for database creator application."""

    def __init__(self):
        """Initialize CLI interface."""
        self.config = load_config()
        self.db_manager = None
        self.templates = DatabaseTemplates()
        # Add advanced templates
        self.templates.add_template(
            "advanced_ecommerce", 
            get_advanced_ecommerce_template()
        )

    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description='Database Creator - Create and manage SQLite databases'
        )
        
        # Main arguments
        parser.add_argument(
            '--db', '-d', 
            help='Database file path', 
            default=self.config.get('last_database', 'database.db')
        )
        parser.add_argument(
            '--template', '-t', 
            help='Use predefined template'
        )
        parser.add_argument(
            '--list-templates', '-l',
            action='store_true',
            help='List available templates'
        )
        parser.add_argument(
            '--export', '-e',
            help='Export database to SQL file'
        )
        parser.add_argument(
            '--import', '-i', 
            dest='import_file',
            help='Import database from SQL file'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command', 
            help='Commands'
        )
        
        # Create table command
        create_parser = subparsers.add_parser(
            'create', 
            help='Create a new table'
        )
        create_parser.add_argument(
            'table_name', 
            help='Name of the table to create'
        )
        create_parser.add_argument(
            '--columns', '-c',
            nargs='+',
            help='Columns definitions in format name:type[:constraints]'
        )
        
        # Insert command
        insert_parser = subparsers.add_parser(
            'insert', 
            help='Insert data into table'
        )
        insert_parser.add_argument(
            'table_name', 
            help='Name of the table'
        )
        insert_parser.add_argument(
            '--values', '-v',
            nargs='+',
            help='Values in format column:value'
        )
        
        # Query command
        query_parser = subparsers.add_parser(
            'query', 
            help='Run SQL query'
        )
        query_parser.add_argument(
            'sql_query', 
            help='SQL query to execute'
        )
        
        # Schema command
        schema_parser = subparsers.add_parser(
            'schema', 
            help='Show database schema'
        )
        
        # Apply template command
        template_parser = subparsers.add_parser(
            'apply-template', 
            help='Apply a template to the database'
        )
        template_parser.add_argument(
            'template_name',
            help='Name of the template to apply'
        )
        
        return parser.parse_args()
    
    def connect_database(self, db_path: str) -> None:
        """Connect to database or create if not exists."""
        self.db_manager = DatabaseManager(db_path)
        self.config['last_database'] = db_path
        save_config(self.config)
        print(f"Connected to database: {db_path}")
    
    def list_templates(self) -> None:
        """List all available templates."""
        print("Available templates:")
        for template_name in self.templates.get_template_names():
            print(f"- {template_name}")
    
    def show_schema(self) -> None:
        """Show the database schema."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        tables = self.db_manager.get_tables()
        if not tables:
            print("Database has no tables.")
            return
        
        print("Database Schema:")
        for table in tables:
            print(f"\nTable: {table}")
            print("-" * (len(table) + 7))
            schema = self.db_manager.get_table_schema(table)
            for col in schema:
                print(f"  {col}")
    
    def apply_template(self, template_name: str) -> None:
        """Apply a template to the database."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        template = self.templates.get_template(template_name)
        if not template:
            print(f"Template '{template_name}' not found.")
            return
        
        print(f"Applying template '{template_name}'...")
        
        try:
            for table_name, table_def in template.items():
                columns = table_def.get('columns', {})
                constraints = table_def.get('constraints', [])
                
                # Format columns for create_table
                column_defs = [f"{name} {dtype}" for name, dtype in columns.items()]
                
                # Add any additional constraints
                if constraints:
                    column_defs.extend(constraints)
                
                # Create the table
                self.db_manager.create_table(table_name, column_defs)
                print(f"Created table: {table_name}")
            
            print(f"Template '{template_name}' applied successfully.")
        except Exception as e:
            print(f"Error applying template: {str(e)}")
    
    def create_table(self, table_name: str, columns: List[str]) -> None:
        """Create a new table with the given columns."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        try:
            self.db_manager.create_table(table_name, columns)
            print(f"Table '{table_name}' created successfully.")
        except Exception as e:
            print(f"Error creating table: {str(e)}")
    
    def insert_data(self, table_name: str, values: List[str]) -> None:
        """Insert data into a table."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        # Parse values from format column:value
        data = {}
        for val in values:
            parts = val.split(':', 1)
            if len(parts) != 2:
                print(f"Invalid value format: {val}, expected column:value")
                continue
            col, value = parts
            data[col] = value
        
        try:
            self.db_manager.insert_into_table(table_name, data)
            print(f"Data inserted into '{table_name}' successfully.")
        except Exception as e:
            print(f"Error inserting data: {str(e)}")
    
    def execute_query(self, query: str) -> None:
        """Execute an arbitrary SQL query."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        try:
            results = self.db_manager.execute_query(query)
            if results:
                # If there are results, try to pretty print them
                if isinstance(results, list) and results and isinstance(results[0], dict):
                    # Print headers
                    headers = results[0].keys()
                    header_str = " | ".join(str(h) for h in headers)
                    print(header_str)
                    print("-" * len(header_str))
                    
                    # Print rows
                    for row in results:
                        print(" | ".join(str(row.get(h, "")) for h in headers))
                else:
                    # Just print the results as is
                    print(results)
            else:
                print("Query executed successfully (no results).")
        except Exception as e:
            print(f"Error executing query: {str(e)}")
    
    def export_database(self, export_path: str) -> None:
        """Export the database to SQL file."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        try:
            self.db_manager.export_to_sql(export_path)
            print(f"Database exported to {export_path}")
        except Exception as e:
            print(f"Error exporting database: {str(e)}")
    
    def import_database(self, import_path: str) -> None:
        """Import the database from SQL file."""
        if not self.db_manager:
            print("No database connected.")
            return
        
        try:
            self.db_manager.import_from_sql(import_path)
            print(f"Database imported from {import_path}")
        except Exception as e:
            print(f"Error importing database: {str(e)}")
    
    def run(self) -> None:
        """Run the CLI application."""
        args = self.parse_arguments()
        
        # Handle list templates command first (doesn't need a db connection)
        if args.list_templates:
            self.list_templates()
            return
        
        # Connect to database
        self.connect_database(args.db)
        
        # Handle direct template application via --template
        if args.template:
            self.apply_template(args.template)
        
        # Handle export/import
        if args.export:
            self.export_database(args.export)
        
        if args.import_file:
            self.import_database(args.import_file)
        
        # Handle commands
        if args.command == 'create' and args.columns:
            self.create_table(args.table_name, args.columns)
        
        elif args.command == 'insert' and args.values:
            self.insert_data(args.table_name, args.values)
        
        elif args.command == 'query':
            self.execute_query(args.sql_query)
        
        elif args.command == 'schema':
            self.show_schema()
        
        elif args.command == 'apply-template':
            self.apply_template(args.template_name)


def main():
    """Entry point for CLI application."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
