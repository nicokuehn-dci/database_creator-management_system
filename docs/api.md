# Database Creator API Reference

This document provides a comprehensive guide to the programmatic API for the Database Creator library.

## Core Modules

The Database Creator package is organized into several modules:

- `database`: Core database operations
- `security`: Security and authentication
- `templates`: Template management
- `config`: Configuration handling
- `cli`: Command-line interface
- `gui`: Graphical user interface

## Database Operations

### Connecting to a Database

```python
from database_creator import DatabaseManager, DatabaseConnection

# Using the high-level manager (recommended)
db_manager = DatabaseManager("path/to/database.db")

# Or using the lower-level connection
db_conn = DatabaseConnection("path/to/database.db")
connection = db_conn.get_connection()
```

### Table Operations

```python
# Create a table
db_manager.create_table(
    "users",
    columns=["id INTEGER PRIMARY KEY", 
             "username TEXT UNIQUE NOT NULL",
             "password TEXT NOT NULL",
             "email TEXT UNIQUE",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"]
)

# Check if a table exists
if db_manager.table_exists("users"):
    print("Table exists!")

# Get table structure
schema = db_manager.get_table_schema("users")
print(schema)

# List all tables
tables = db_manager.list_tables()
print(tables)

# Drop a table
db_manager.drop_table("old_table")
```

### Data Operations

```python
# Insert data
user_data = {
    "username": "john_doe",
    "password": hashed_password,
    "email": "john@example.com"
}
db_manager.insert_into_table("users", user_data)

# Batch insert
users = [
    {"username": "user1", "password": "hash1", "email": "user1@example.com"},
    {"username": "user2", "password": "hash2", "email": "user2@example.com"}
]
db_manager.batch_insert("users", users)

# Update data
update_data = {"email": "newemail@example.com"}
where_clause = "username = 'john_doe'"
db_manager.update_table("users", update_data, where_clause)

# Delete data
db_manager.delete_from_table("users", "username = 'user_to_delete'")

# Execute a custom query
results = db_manager.execute_query("SELECT * FROM users WHERE id > 10")
for row in results:
    print(row)
```

### Transaction Handling

```python
# Using context manager for transactions
with db_manager.transaction():
    db_manager.insert_into_table("users", user1_data)
    db_manager.insert_into_table("profiles", profile1_data)
    # If any error occurs, all changes will be rolled back
```

## Security Functions

### Password Handling

```python
from database_creator.security import hash_password, verify_password

# Hash a password (returns the hash and salt)
hashed_password, salt = hash_password("secure_password")

# Verify a password
is_valid = verify_password(hashed_password, "provided_password")
if is_valid:
    print("Password is correct!")
else:
    print("Password is incorrect!")
```

### Input Validation

```python
from database_creator.security import (
    validate_string, validate_email, validate_number, sanitize_input
)

# Validate a string input
is_valid, sanitized = validate_string(
    user_input, 
    min_length=3,
    max_length=50,
    pattern=r'^[A-Za-z0-9_]+$'
)

# Validate an email
is_valid, sanitized = validate_email(email_input)

# Validate a number
is_valid, number = validate_number(
    number_input, 
    min_val=0, 
    max_val=100
)

# Sanitize input for SQL queries
safe_input = sanitize_input(user_input)
```

## Template Management

### Using Templates

```python
from database_creator import DatabaseManager
from database_creator.templates import DatabaseTemplates

# Initialize objects
db_manager = DatabaseManager("new_db.db")
templates = DatabaseTemplates()

# List available templates
template_list = templates.list_templates()
print(template_list)

# Get details of a specific template
template_info = templates.get_template_info("web_store")
print(template_info["description"])
print(f"Number of tables: {len(template_info['tables'])}")

# Apply a template
success = templates.apply_template(db_manager, "simple_blog")
if success:
    print("Template applied successfully!")
```

### Creating Custom Templates

```python
# Define a custom template
contact_book = {
    "contacts": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "email": "TEXT",
            "phone": "TEXT",
            "notes": "TEXT"
        }
    },
    "groups": {
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "description": "TEXT"
        }
    },
    "contact_groups": {
        "columns": {
            "contact_id": "INTEGER",
            "group_id": "INTEGER"
        },
        "constraints": [
            "PRIMARY KEY (contact_id, group_id)",
            "FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE",
            "FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE"
        ]
    }
}

# Save the template
templates.save_template(
    name="contact_book",
    description="A simple contact management system",
    tables=contact_book
)
```

## Configuration Management

```python
from database_creator.config import load_config, save_config

# Load configuration
config = load_config()

# Access configuration values
default_path = config.get("default_path", os.getcwd())
recent_dbs = config.get("recent_databases", [])

# Update configuration
config["max_recent"] = 10
config["recent_databases"].append("path/to/new_db.db")

# Save configuration
save_config(config)
```

## CLI Interface

```python
from database_creator.cli import CLI

# Create a CLI instance
cli = CLI()

# Parse arguments from command line
args = cli.parse_args()

# Run a specific command
cli.run_command("create_table", table_name="products", columns=[
    "id INTEGER PRIMARY KEY",
    "name TEXT NOT NULL",
    "price REAL"
])

# Or run the CLI interface
cli.run()
```

## GUI Interface

```python
from database_creator.gui import GUI

# Create a GUI instance
gui = GUI()

# Connect to a database
gui.connect_database("path/to/database.db")

# Run the GUI
gui.run()
```

## Advanced Usage

### Custom SQL Functions

```python
# Register a custom SQL function
def calculate_discount(price, percentage):
    return price - (price * percentage / 100)

db_manager.register_function("discount", calculate_discount)

# Now you can use this in SQL queries
results = db_manager.execute_query(
    "SELECT name, price, discount(price, 10) AS sale_price FROM products"
)
```

### Export/Import

```python
# Export database to SQL file
db_manager.export_to_sql("backup.sql")

# Export table to CSV
db_manager.export_table_to_csv("users", "users.csv")

# Import from SQL file
db_manager.import_from_sql("backup.sql")

# Import from CSV
db_manager.import_from_csv("products", "products.csv", 
                          {"id": "INTEGER", "name": "TEXT", "price": "REAL"})
```

### Event Hooks

```python
# Register event hooks
db_manager.on_before_table_create(lambda table_name: print(f"Creating {table_name}..."))
db_manager.on_after_table_create(lambda table_name: print(f"Created {table_name}!"))

# Or with decorator syntax
@db_manager.before_table_drop
def confirm_drop(table_name):
    return input(f"Really drop {table_name}? (y/n): ").lower() == 'y'
```
