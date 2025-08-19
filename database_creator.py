import sqlite3
import os
import json
import re
import hashlib
import secrets
import datetime
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Constants
DEFAULT_DB_NAME = "database.db"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".database_creator")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TEMPLATES_DIR = os.path.join(CONFIG_DIR, "templates")

# Create configuration directory if it doesn't exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "recent_databases": [],
    "max_recent": 5,
    "default_path": os.getcwd(),
    "use_secure_passwords": True,
    "password_min_length": 8,
    "export_formats": ["sql", "csv", "json"],
    "templates": []
}

# Load or create configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Config file corrupted. Using default configuration.")
            return DEFAULT_CONFIG
    else:
        # Create default config
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Secure hash function for passwords
def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
    """Hash a password for storing."""
    if salt is None:
        salt = secrets.token_bytes(32)
    
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{pwdhash.hex()}", salt

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    salt_hex, key_hex = stored_password.split(':')
    salt = bytes.fromhex(salt_hex)
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash.hex() == key_hex

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
        self.db_path = db_path
        self.config = load_config()
        
        # Add to recent databases
        if db_path not in self.config["recent_databases"]:
            self.config["recent_databases"].insert(0, db_path)
            self.config["recent_databases"] = self.config["recent_databases"][:self.config["max_recent"]]
            save_config(self.config)
    
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
                
                # For SELECT queries
                if query.strip().upper().startswith("SELECT"):
                    return [dict(row) for row in cursor.fetchall()]
                
                # For other queries (INSERT, UPDATE, DELETE)
                return [{"rowcount": cursor.rowcount}]
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return []
    
    def create_table(self, table_name: str, columns: Dict[str, str], 
                     constraints: List[str] = None) -> bool:
        """
        Create a table with the given name and columns.
        
        Args:
            table_name: Name of the table
            columns: Dictionary mapping column names to their types and constraints
            constraints: List of table-level constraints
        """
        try:
            column_defs = []
            for col_name, col_def in columns.items():
                column_defs.append(f"{col_name} {col_def}")
            
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
            with open(json_file, 'r') as f:
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

# Database templates manager
class DatabaseTemplates:
    def __init__(self, templates_dir=TEMPLATES_DIR):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        
    def list_templates(self):
        """List all available templates."""
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_path = os.path.join(self.templates_dir, filename)
                try:
                    with open(template_path, 'r') as f:
                        template = json.load(f)
                    templates.append(template)
                except json.JSONDecodeError:
                    pass  # Skip invalid templates
        return templates
    
    def save_template(self, name, description, tables):
        """Save a database template."""
        template = {
            "name": name,
            "description": description,
            "created": datetime.datetime.now().isoformat(),
            "tables": tables
        }
        
        # Create a valid filename from template name
        filename = re.sub(r'[^\w\s-]', '', name.lower())
        filename = re.sub(r'[-\s]+', '_', filename)
        template_path = os.path.join(self.templates_dir, f"{filename}.json")
        
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        return template_path
    
    def load_template(self, template_name):
        """Load a template by name."""
        filename = f"{template_name.lower().replace(' ', '_')}.json"
        template_path = os.path.join(self.templates_dir, filename)
        
        if not os.path.exists(template_path):
            return None
        
        try:
            with open(template_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    def apply_template(self, db_manager, template_name):
        """Apply a template to a database."""
        template = self.load_template(template_name)
        if not template:
            print(f"❌ Template '{template_name}' not found.")
            return False
        
        for table_name, table_def in template['tables'].items():
            columns = table_def['columns']
            constraints = table_def.get('constraints', [])
            db_manager.create_table(table_name, columns, constraints)
        
        return True

# Initialize templates with defaults if empty
def initialize_default_templates():
    templates = DatabaseTemplates()
    
    # If no templates exist, create defaults
    if not os.listdir(TEMPLATES_DIR):
        # Web Store Template
        web_store = {
            "customers": {
                "columns": {
                    "customer_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "first_name": "TEXT NOT NULL",
                    "last_name": "TEXT NOT NULL",
                    "email": "TEXT UNIQUE NOT NULL",
                    "password_hash": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            },
            "products": {
                "columns": {
                    "product_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "description": "TEXT",
                    "price": "REAL NOT NULL",
                    "stock": "INTEGER DEFAULT 0",
                    "category": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            },
            "orders": {
                "columns": {
                    "order_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "customer_id": "INTEGER NOT NULL",
                    "total_amount": "REAL NOT NULL",
                    "status": "TEXT DEFAULT 'pending'",
                    "order_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                },
                "constraints": [
                    "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)"
                ]
            },
            "order_items": {
                "columns": {
                    "item_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "order_id": "INTEGER NOT NULL",
                    "product_id": "INTEGER NOT NULL",
                    "quantity": "INTEGER NOT NULL",
                    "price": "REAL NOT NULL"
                },
                "constraints": [
                    "FOREIGN KEY (order_id) REFERENCES orders(order_id)",
                    "FOREIGN KEY (product_id) REFERENCES products(product_id)"
                ]
            }
        }
        templates.save_template(
            "Web Store", 
            "A complete e-commerce database with customers, products, orders, and line items",
            web_store
        )
        
        # Music Library Template
        music_library = {
            "artists": {
                "columns": {
                    "artist_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "country": "TEXT",
                    "formed_year": "INTEGER",
                    "bio": "TEXT"
                }
            },
            "albums": {
                "columns": {
                    "album_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "title": "TEXT NOT NULL",
                    "artist_id": "INTEGER NOT NULL",
                    "release_year": "INTEGER",
                    "genre": "TEXT",
                    "cover_art": "TEXT"
                },
                "constraints": [
                    "FOREIGN KEY (artist_id) REFERENCES artists(artist_id)"
                ]
            },
            "songs": {
                "columns": {
                    "song_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "title": "TEXT NOT NULL",
                    "album_id": "INTEGER NOT NULL",
                    "track_number": "INTEGER",
                    "duration": "INTEGER",
                    "lyrics": "TEXT"
                },
                "constraints": [
                    "FOREIGN KEY (album_id) REFERENCES albums(album_id)"
                ]
            },
            "playlists": {
                "columns": {
                    "playlist_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "description": "TEXT"
                }
            },
            "playlist_songs": {
                "columns": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "playlist_id": "INTEGER NOT NULL",
                    "song_id": "INTEGER NOT NULL",
                    "position": "INTEGER"
                },
                "constraints": [
                    "FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id)",
                    "FOREIGN KEY (song_id) REFERENCES songs(song_id)"
                ]
            }
        }
        templates.save_template(
            "Music Library", 
            "A music collection database with artists, albums, songs, and playlists",
            music_library
        )
        
        # Task Manager Template
        task_manager = {
            "users": {
                "columns": {
                    "user_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "username": "TEXT UNIQUE NOT NULL",
                    "email": "TEXT UNIQUE NOT NULL",
                    "password_hash": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            },
            "projects": {
                "columns": {
                    "project_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "description": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "owner_id": "INTEGER NOT NULL"
                },
                "constraints": [
                    "FOREIGN KEY (owner_id) REFERENCES users(user_id)"
                ]
            },
            "tasks": {
                "columns": {
                    "task_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "project_id": "INTEGER NOT NULL",
                    "title": "TEXT NOT NULL",
                    "description": "TEXT",
                    "due_date": "TIMESTAMP",
                    "priority": "INTEGER DEFAULT 0",
                    "status": "TEXT DEFAULT 'todo'",
                    "assigned_to": "INTEGER",
                    "created_by": "INTEGER NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                },
                "constraints": [
                    "FOREIGN KEY (project_id) REFERENCES projects(project_id)",
                    "FOREIGN KEY (assigned_to) REFERENCES users(user_id)",
                    "FOREIGN KEY (created_by) REFERENCES users(user_id)"
                ]
            },
            "comments": {
                "columns": {
                    "comment_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "task_id": "INTEGER NOT NULL",
                    "user_id": "INTEGER NOT NULL",
                    "content": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                },
                "constraints": [
                    "FOREIGN KEY (task_id) REFERENCES tasks(task_id)",
                    "FOREIGN KEY (user_id) REFERENCES users(user_id)"
                ]
            }
        }
        templates.save_template(
            "Task Manager", 
            "A project management database with users, projects, tasks, and comments",
            task_manager
        )
        
        # Blog System Template
        blog_system = {
            "users": {
                "columns": {
                    "user_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "username": "TEXT UNIQUE NOT NULL",
                    "email": "TEXT UNIQUE NOT NULL",
                    "password_hash": "TEXT NOT NULL",
                    "bio": "TEXT",
                    "is_admin": "BOOLEAN DEFAULT 0",
                    "joined_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            },
            "categories": {
                "columns": {
                    "category_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT UNIQUE NOT NULL",
                    "description": "TEXT"
                }
            },
            "posts": {
                "columns": {
                    "post_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "title": "TEXT NOT NULL",
                    "content": "TEXT NOT NULL",
                    "user_id": "INTEGER NOT NULL",
                    "category_id": "INTEGER",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "published": "BOOLEAN DEFAULT 1"
                },
                "constraints": [
                    "FOREIGN KEY (user_id) REFERENCES users(user_id)",
                    "FOREIGN KEY (category_id) REFERENCES categories(category_id)"
                ]
            },
            "comments": {
                "columns": {
                    "comment_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "post_id": "INTEGER NOT NULL",
                    "user_id": "INTEGER NOT NULL",
                    "content": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "approved": "BOOLEAN DEFAULT 0"
                },
                "constraints": [
                    "FOREIGN KEY (post_id) REFERENCES posts(post_id)",
                    "FOREIGN KEY (user_id) REFERENCES users(user_id)"
                ]
            },
            "tags": {
                "columns": {
                    "tag_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT UNIQUE NOT NULL"
                }
            },
            "post_tags": {
                "columns": {
                    "post_id": "INTEGER NOT NULL",
                    "tag_id": "INTEGER NOT NULL"
                },
                "constraints": [
                    "PRIMARY KEY (post_id, tag_id)",
                    "FOREIGN KEY (post_id) REFERENCES posts(post_id)",
                    "FOREIGN KEY (tag_id) REFERENCES tags(tag_id)"
                ]
            }
        }
        templates.save_template(
            "Blog System", 
            "A blogging database with users, posts, comments, categories, and tags",
            blog_system
        )
        
        # Advanced E-Commerce Template
        advanced_ecommerce = {
            "customers": {
                "columns": {
                    "customer_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "first_name": "TEXT NOT NULL",
                    "last_name": "TEXT NOT NULL",
                    "email": "TEXT UNIQUE NOT NULL",
                    "password_hash": "TEXT NOT NULL",
                    "phone": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "last_login": "TIMESTAMP",
                    "status": "TEXT DEFAULT 'active'"
                }
            },
            "customer_addresses": {
                "columns": {
                    "address_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "customer_id": "INTEGER NOT NULL",
                    "address_type": "TEXT DEFAULT 'shipping'",
                    "street": "TEXT NOT NULL",
                    "city": "TEXT NOT NULL",
                    "state": "TEXT NOT NULL",
                    "zip_code": "TEXT NOT NULL",
                    "country": "TEXT NOT NULL",
                    "is_default": "BOOLEAN DEFAULT 0"
                },
                "constraints": [
                    "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)"
                ]
            },
            "categories": {
                "columns": {
                    "category_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "description": "TEXT",
                    "parent_id": "INTEGER",
                    "image_url": "TEXT",
                    "active": "BOOLEAN DEFAULT 1"
                },
                "constraints": [
                    "FOREIGN KEY (parent_id) REFERENCES categories(category_id)"
                ]
            },
            "suppliers": {
                "columns": {
                    "supplier_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "contact_name": "TEXT",
                    "email": "TEXT",
                    "phone": "TEXT",
                    "address": "TEXT",
                    "website": "TEXT",
                    "notes": "TEXT"
                }
            },
            "products": {
                "columns": {
                    "product_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "sku": "TEXT UNIQUE",
                    "name": "TEXT NOT NULL",
                    "description": "TEXT",
                    "price": "REAL NOT NULL",
                    "cost": "REAL",
                    "category_id": "INTEGER",
                    "supplier_id": "INTEGER",
                    "stock": "INTEGER DEFAULT 0",
                    "weight": "REAL",
                    "dimensions": "TEXT",
                    "image_url": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "active": "BOOLEAN DEFAULT 1"
                },
                "constraints": [
                    "FOREIGN KEY (category_id) REFERENCES categories(category_id)",
                    "FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)"
                ]
            },
            "product_attributes": {
                "columns": {
                    "attribute_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "product_id": "INTEGER NOT NULL",
                    "name": "TEXT NOT NULL",
                    "value": "TEXT NOT NULL"
                },
                "constraints": [
                    "FOREIGN KEY (product_id) REFERENCES products(product_id)"
                ]
            },
            "inventory_locations": {
                "columns": {
                    "location_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "name": "TEXT NOT NULL",
                    "address": "TEXT",
                    "type": "TEXT DEFAULT 'warehouse'"
                }
            },
            "inventory": {
                "columns": {
                    "inventory_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "product_id": "INTEGER NOT NULL",
                    "location_id": "INTEGER NOT NULL",
                    "quantity": "INTEGER NOT NULL DEFAULT 0",
                    "last_updated": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                },
                "constraints": [
                    "FOREIGN KEY (product_id) REFERENCES products(product_id)",
                    "FOREIGN KEY (location_id) REFERENCES inventory_locations(location_id)"
                ]
            },
            "purchase_orders": {
                "columns": {
                    "po_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "supplier_id": "INTEGER NOT NULL",
                    "order_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "delivery_date": "TIMESTAMP",
                    "status": "TEXT DEFAULT 'pending'",
                    "total_amount": "REAL",
                    "notes": "TEXT"
                },
                "constraints": [
                    "FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)"
                ]
            },
            "purchase_order_items": {
                "columns": {
                    "item_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "po_id": "INTEGER NOT NULL",
                    "product_id": "INTEGER NOT NULL",
                    "quantity": "INTEGER NOT NULL",
                    "unit_price": "REAL NOT NULL",
                    "received_quantity": "INTEGER DEFAULT 0"
                },
                "constraints": [
                    "FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)",
                    "FOREIGN KEY (product_id) REFERENCES products(product_id)"
                ]
            },
            "orders": {
                "columns": {
                    "order_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "customer_id": "INTEGER NOT NULL",
                    "order_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "shipping_address_id": "INTEGER",
                    "billing_address_id": "INTEGER",
                    "shipping_method": "TEXT",
                    "payment_method": "TEXT",
                    "subtotal": "REAL NOT NULL",
                    "tax": "REAL DEFAULT 0",
                    "shipping_cost": "REAL DEFAULT 0",
                    "total_amount": "REAL NOT NULL",
                    "status": "TEXT DEFAULT 'pending'",
                    "notes": "TEXT"
                },
                "constraints": [
                    "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)",
                    "FOREIGN KEY (shipping_address_id) REFERENCES customer_addresses(address_id)",
                    "FOREIGN KEY (billing_address_id) REFERENCES customer_addresses(address_id)"
                ]
            },
            "order_items": {
                "columns": {
                    "item_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "order_id": "INTEGER NOT NULL",
                    "product_id": "INTEGER NOT NULL",
                    "quantity": "INTEGER NOT NULL",
                    "unit_price": "REAL NOT NULL",
                    "subtotal": "REAL NOT NULL",
                    "discount": "REAL DEFAULT 0"
                },
                "constraints": [
                    "FOREIGN KEY (order_id) REFERENCES orders(order_id)",
                    "FOREIGN KEY (product_id) REFERENCES products(product_id)"
                ]
            },
            "payments": {
                "columns": {
                    "payment_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "order_id": "INTEGER NOT NULL",
                    "amount": "REAL NOT NULL",
                    "payment_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "payment_method": "TEXT NOT NULL",
                    "transaction_id": "TEXT",
                    "status": "TEXT DEFAULT 'completed'"
                },
                "constraints": [
                    "FOREIGN KEY (order_id) REFERENCES orders(order_id)"
                ]
            },
            "shipments": {
                "columns": {
                    "shipment_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "order_id": "INTEGER NOT NULL",
                    "tracking_number": "TEXT",
                    "carrier": "TEXT",
                    "ship_date": "TIMESTAMP",
                    "delivery_date": "TIMESTAMP",
                    "status": "TEXT DEFAULT 'processing'"
                },
                "constraints": [
                    "FOREIGN KEY (order_id) REFERENCES orders(order_id)"
                ]
            },
            "reviews": {
                "columns": {
                    "review_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "product_id": "INTEGER NOT NULL",
                    "customer_id": "INTEGER NOT NULL",
                    "rating": "INTEGER NOT NULL",
                    "review_text": "TEXT",
                    "review_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "approved": "BOOLEAN DEFAULT 0"
                },
                "constraints": [
                    "FOREIGN KEY (product_id) REFERENCES products(product_id)",
                    "FOREIGN KEY (customer_id) REFERENCES customers(customer_id)"
                ]
            },
            "discounts": {
                "columns": {
                    "discount_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "code": "TEXT UNIQUE",
                    "description": "TEXT",
                    "amount": "REAL NOT NULL",
                    "is_percentage": "BOOLEAN DEFAULT 1",
                    "start_date": "TIMESTAMP",
                    "end_date": "TIMESTAMP",
                    "min_order_amount": "REAL DEFAULT 0",
                    "max_uses": "INTEGER",
                    "current_uses": "INTEGER DEFAULT 0",
                    "active": "BOOLEAN DEFAULT 1"
                }
            }
        }
        templates.save_template(
            "Advanced E-Commerce", 
            "A comprehensive e-commerce database with customers, products, inventory, orders, payments, and more",
            advanced_ecommerce
        )

# Initialize default templates
initialize_default_templates()

# Validator class for data validation
class Validator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate an email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, message)
        """
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long"
        
        checks = [
            (re.search(r'[A-Z]', password), "at least one uppercase letter"),
            (re.search(r'[a-z]', password), "at least one lowercase letter"),
            (re.search(r'[0-9]', password), "at least one number"),
            (re.search(r'[^A-Za-z0-9]', password), "at least one special character")
        ]
        
        failed_checks = [msg for check, msg in checks if not check]
        
        if failed_checks:
            return False, "Password must contain " + ", ".join(failed_checks)
        
        return True, "Password is strong"
    
    @staticmethod
    def validate_number(value: str, min_val: float = None, max_val: float = None) -> Tuple[bool, Union[int, float, None]]:
        """
        Validate if a string is a valid number.
        Returns (is_valid, converted_value)
        """
        try:
            # Try as integer first
            num = int(value)
            if "." in value:  # If it had a decimal point, convert to float
                num = float(value)
        except ValueError:
            try:
                # Try as float
                num = float(value)
            except ValueError:
                return False, None
        
        # Check range if specified
        if min_val is not None and num < min_val:
            return False, None
        if max_val is not None and num > max_val:
            return False, None
            
        return True, num

# Database schema setup functions
def setup_database(db_manager):
    """Set up a database with default schema based on template."""
    templates = DatabaseTemplates()
    template_list = templates.list_templates()
    
    if not template_list:
        print("❌ No templates available. Creating default structure...")
        initialize_default_templates()
        template_list = templates.list_templates()
    
    print("\n=== Available Database Templates ===")
    for i, template in enumerate(template_list):
        print(f"{i+1}. {template['name']} - {template['description']}")
    print("0. Custom database (define your own schema)")
    
    choice = input("\nSelect a template (or 0 for custom): ")
    
    if choice == "0":
        return setup_custom_database(db_manager)
    else:
        try:
            index = int(choice) - 1
            if 0 <= index < len(template_list):
                template = template_list[index]
                print(f"\nApplying template: {template['name']}")
                
                # Create tables from template
                for table_name, table_def in template['tables'].items():
                    columns = table_def.get('columns', {})
                    constraints = table_def.get('constraints', [])
                    
                    if db_manager.create_table(table_name, columns, constraints):
                        print(f"✅ Created table: {table_name}")
                    else:
                        print(f"❌ Failed to create table: {table_name}")
                
                return True
            else:
                print("❌ Invalid choice. Please try again.")
                return False
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
            return False

def setup_custom_database(db_manager):
    """Set up a custom database schema interactively."""
    print("\n=== Custom Database Setup ===")
    print("You'll now define the tables for your database.")
    
    tables_created = 0
    
    while True:
        table_name = input("\nEnter table name (or press Enter to finish): ")
        if not table_name:
            break
        
        columns = {}
        constraints = []
        
        print(f"\nDefining columns for table '{table_name}':")
        print("For each column, provide name and definition (e.g., TEXT NOT NULL)")
        
        while True:
            col_name = input("\nColumn name (or press Enter to finish columns): ")
            if not col_name:
                break
            
            col_def = input(f"Definition for '{col_name}' (e.g., INTEGER PRIMARY KEY): ")
            columns[col_name] = col_def
        
        print("\nAdd table constraints (e.g., FOREIGN KEY, UNIQUE):")
        print("Enter constraints one by one, or press Enter to skip")
        
        while True:
            constraint = input("Constraint (or press Enter to finish): ")
            if not constraint:
                break
            constraints.append(constraint)
        
        if db_manager.create_table(table_name, columns, constraints):
            print(f"✅ Table '{table_name}' created successfully.")
            tables_created += 1
        else:
            print(f"❌ Failed to create table '{table_name}'.")
    
    if tables_created > 0:
        print(f"\n✅ Database setup complete. Created {tables_created} tables.")
        return True
    else:
        print("\n⚠️ No tables were created.")
        return False

def add_customer(db_manager):
    """Add a customer to the database with secure password handling."""
    print("\n=== Add Customer ===")
    
    if not db_manager.table_exists("customers"):
        print("❌ Customers table does not exist. Please set up the database first.")
        return
    
    first_name = input("First name: ")
    last_name = input("Last name: ")
    email = input("Email: ")
    
    # Validate email
    if not Validator.validate_email(email):
        print("❌ Invalid email format.")
        return
    
    # Check if email already exists
    existing = db_manager.execute_query(
        "SELECT customer_id FROM customers WHERE email = ?", 
        (email,)
    )
    if existing:
        print("❌ A customer with this email already exists.")
        return
    
    password = input("Password: ")
    
    # Validate password
    config = load_config()
    is_valid, message = Validator.validate_password(password, config.get("password_min_length", 8))
    
    if not is_valid:
        print(f"❌ {message}")
        return
    
    # Hash password
    password_hash, _ = hash_password(password)
    
    # Insert into database
    result = db_manager.execute_query(
        """
        INSERT INTO customers (first_name, last_name, email, password_hash) 
        VALUES (?, ?, ?, ?)
        """, 
        (first_name, last_name, email, password_hash)
    )
    
    if result:
        print("✅ Customer added successfully.")
    else:
        print("❌ Failed to add customer.")

def add_product(db_manager):
    """Add a product to the database with validation."""
    print("\n=== Add Product ===")
    
    if not db_manager.table_exists("products"):
        print("❌ Products table does not exist. Please set up the database first.")
        return
    
    name = input("Product name: ")
    
    # Get and validate price
    price_str = input("Price: ")
    is_valid, price = Validator.validate_number(price_str, min_val=0)
    if not is_valid:
        print("❌ Invalid price. Must be a positive number.")
        return
    
    # Get and validate stock
    stock_str = input("Stock: ")
    is_valid, stock = Validator.validate_number(stock_str, min_val=0)
    if not is_valid:
        print("❌ Invalid stock. Must be a non-negative integer.")
        return
    stock = int(stock)
    
    # Description is optional
    description = input("Description (optional): ")
    
    # Insert into database
    columns = ["name", "price", "stock"]
    values = [name, price, stock]
    
    # Add description if provided
    if description:
        columns.append("description")
        values.append(description)
    
    query = f"""
    INSERT INTO products ({', '.join(columns)}) 
    VALUES ({', '.join(['?'] * len(values))})
    """
    
    result = db_manager.execute_query(query, tuple(values))
    
    if result:
        print("✅ Product added successfully.")
    else:
        print("❌ Failed to add product.")

def list_products(db_manager):
    """List all products in the database."""
    print("\n=== Products List ===")
    
    if not db_manager.table_exists("products"):
        print("❌ Products table does not exist. Please set up the database first.")
        return
    
    products = db_manager.execute_query(
        """
        SELECT product_id, name, price, stock, description
        FROM products
        ORDER BY product_id
        """
    )
    
    if not products:
        print("No products found.")
        return
    
    print(f"\n{'ID':<5} {'Name':<20} {'Price':<10} {'Stock':<10} {'Description'}")
    print("-" * 70)
    
    for product in products:
        desc = product.get('description', '')
        if desc and len(desc) > 30:
            desc = desc[:27] + "..."
        print(f"{product['product_id']:<5} {product['name']:<20} ${product['price']:<9.2f} {product['stock']:<10} {desc}")

def place_order(db_manager):
    """Place an order with validation and transaction support."""
    print("\n=== Place Order ===")
    
    if not db_manager.table_exists("orders") or not db_manager.table_exists("products"):
        print("❌ Required tables do not exist. Please set up the database first.")
        return
    
    # Get and validate customer ID
    customer_id_str = input("Customer ID: ")
    is_valid, customer_id = Validator.validate_number(customer_id_str, min_val=1)
    if not is_valid:
        print("❌ Invalid customer ID.")
        return
    
    # Check if customer exists
    customer = db_manager.execute_query(
        "SELECT customer_id FROM customers WHERE customer_id = ?", 
        (customer_id,)
    )
    if not customer:
        print("❌ Customer not found.")
        return
    
    # List products for selection
    list_products(db_manager)
    
    # Get and validate product ID
    product_id_str = input("\nProduct ID: ")
    is_valid, product_id = Validator.validate_number(product_id_str, min_val=1)
    if not is_valid:
        print("❌ Invalid product ID.")
        return
    
    # Check product and stock
    product = db_manager.execute_query(
        "SELECT product_id, name, price, stock FROM products WHERE product_id = ?", 
        (product_id,)
    )
    if not product:
        print("❌ Product not found.")
        return
    
    product = product[0]
    
    # Get and validate quantity
    quantity_str = input("Quantity: ")
    is_valid, quantity = Validator.validate_number(quantity_str, min_val=1)
    if not is_valid:
        print("❌ Invalid quantity. Must be a positive integer.")
        return
    quantity = int(quantity)
    
    # Check if enough stock
    if product['stock'] < quantity:
        print("❌ Not enough stock available.")
        return
    
    # Calculate total amount
    total_amount = product['price'] * quantity
    
    # Start a transaction to ensure consistency
    try:
        with DatabaseConnection(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert order
            cursor.execute(
                """
                INSERT INTO orders (customer_id, total_amount) 
                VALUES (?, ?)
                """, 
                (customer_id, total_amount)
            )
            
            order_id = cursor.lastrowid
            
            # Insert order item
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, price) 
                VALUES (?, ?, ?, ?)
                """, 
                (order_id, product_id, quantity, product['price'])
            )
            
            # Update stock
            cursor.execute(
                """
                UPDATE products SET stock = stock - ? WHERE product_id = ?
                """, 
                (quantity, product_id)
            )
        
        print(f"✅ Order #{order_id} placed successfully.")
        print(f"Total amount: ${total_amount:.2f}")
        
    except sqlite3.Error as e:
        print(f"❌ Error placing order: {e}")

def list_orders(db_manager):
    """List all orders with details."""
    print("\n=== Orders List ===")
    
    if not db_manager.table_exists("orders"):
        print("❌ Orders table does not exist. Please set up the database first.")
        return
    
    # Check if we have the old schema or the new schema
    table_info = db_manager.get_table_info("orders")
    column_names = [col['name'] for col in table_info]
    
    if 'product_id' in column_names:
        # Old schema with direct product reference
        orders = db_manager.execute_query(
            """
            SELECT o.order_id, c.first_name || ' ' || c.last_name AS customer_name,
                   p.name AS product_name, o.quantity, o.order_date,
                   p.price * o.quantity AS total
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN products p ON o.product_id = p.product_id
            ORDER BY o.order_date DESC
            """
        )
        
        if not orders:
            print("No orders found.")
            return
        
        print(f"\n{'ID':<5} {'Customer':<20} {'Product':<20} {'Quantity':<10} {'Date':<20} {'Total'}")
        print("-" * 90)
        
        for order in orders:
            print(f"{order['order_id']:<5} {order['customer_name']:<20} {order['product_name']:<20} "
                  f"{order['quantity']:<10} {order['order_date']:<20} ${order['total']:.2f}")
    else:
        # New schema with order_items table
        try:
            orders = db_manager.execute_query(
                """
                SELECT o.order_id, c.first_name || ' ' || c.last_name AS customer_name,
                       o.order_date, o.total_amount, o.status
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                ORDER BY o.order_date DESC
                """
            )
            
            if not orders:
                print("No orders found.")
                return
            
            print(f"\n{'ID':<5} {'Customer':<20} {'Date':<20} {'Status':<10} {'Total'}")
            print("-" * 70)
            
            for order in orders:
                print(f"{order['order_id']:<5} {order['customer_name']:<20} {order['order_date']:<20} "
                      f"{order['status']:<10} ${order['total_amount']:.2f}")
                
                # Get order items
                items = db_manager.execute_query(
                    """
                    SELECT oi.product_id, p.name AS product_name, oi.quantity, oi.price
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.product_id
                    WHERE oi.order_id = ?
                    """,
                    (order['order_id'],)
                )
                
                if items:
                    print(f"   Items:")
                    for item in items:
                        item_total = item['quantity'] * item['price']
                        print(f"   - {item['product_name']} x{item['quantity']} @ ${item['price']:.2f} = ${item_total:.2f}")
                    print()
        except sqlite3.Error:
            print("❌ Error retrieving orders. Schema might be incompatible.")

def export_database(db_manager):
    """Export database to various formats."""
    print("\n=== Export Database ===")
    
    config = load_config()
    formats = config.get("export_formats", ["sql", "csv", "json"])
    
    print("Available export formats:")
    for i, format_type in enumerate(formats):
        print(f"{i+1}. {format_type.upper()}")
    
    try:
        choice = int(input("\nSelect format: "))
        if choice < 1 or choice > len(formats):
            print("❌ Invalid choice.")
            return
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return
    
    format_type = formats[choice-1]
    
    # Get output path
    if format_type == 'csv':
        default_path = f"{os.path.splitext(db_manager.db_path)[0]}_export"
        output_path = input(f"Output directory path [{default_path}]: ") or default_path
    else:
        default_path = f"{os.path.splitext(db_manager.db_path)[0]}.{format_type}"
        output_path = input(f"Output file path [{default_path}]: ") or default_path
    
    print(f"\nExporting to {format_type.upper()}...")
    if db_manager.export_database(format_type, output_path):
        print(f"✅ Database exported successfully to {output_path}")
    else:
        print("❌ Export failed.")

def import_database(db_manager):
    """Import database from SQL or JSON file."""
    print("\n=== Import Database ===")
    print("Warning: This will overwrite existing tables!")
    
    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Import cancelled.")
        return
    
    print("\nAvailable import formats:")
    print("1. SQL")
    print("2. JSON")
    
    try:
        choice = int(input("\nSelect format: "))
        if choice < 1 or choice > 2:
            print("❌ Invalid choice.")
            return
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return
    
    # Get input file
    file_path = input("Input file path: ")
    if not os.path.exists(file_path):
        print("❌ File not found.")
        return
    
    print("\nImporting data...")
    success = False
    
    if choice == 1:  # SQL
        success = db_manager.import_from_sql(file_path)
    else:  # JSON
        success = db_manager.import_from_json(file_path)
    
    if success:
        print("✅ Database imported successfully.")
    else:
        print("❌ Import failed.")

def save_current_as_template(db_manager):
    """Save the current database schema as a template."""
    print("\n=== Save as Template ===")
    
    name = input("Template name: ")
    if not name:
        print("❌ Template name is required.")
        return
    
    description = input("Description: ")
    
    # Get all tables
    tables = db_manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    
    if not tables:
        print("❌ No tables found in the database.")
        return
    
    template_tables = {}
    
    for table in tables:
        table_name = table['name']
        
        # Get columns
        columns_info = db_manager.get_table_info(table_name)
        
        # Format columns
        columns = {}
        for col in columns_info:
            col_def = f"{col['type']}"
            if col['notnull']:
                col_def += " NOT NULL"
            if col['pk']:
                col_def += " PRIMARY KEY"
            if col['dflt_value'] is not None:
                col_def += f" DEFAULT {col['dflt_value']}"
                
            columns[col['name']] = col_def
        
        # Get constraints (simplified - just foreign keys for now)
        constraints = []
        try:
            fk_info = db_manager.execute_query(f"PRAGMA foreign_key_list({table_name});")
            for fk in fk_info:
                constraint = f"FOREIGN KEY ({fk['from']}) REFERENCES {fk['table']}({fk['to']})"
                constraints.append(constraint)
        except:
            pass
        
        template_tables[table_name] = {
            "columns": columns,
            "constraints": constraints
        }
    
    # Save template
    templates = DatabaseTemplates()
    template_path = templates.save_template(name, description, template_tables)
    
    print(f"✅ Template saved: {template_path}")

def menu(db_path=None):
    """Main menu for the database creator application."""
    
    if db_path is None:
        # Get recent databases
        config = load_config()
        recent_dbs = config.get("recent_databases", [])
        
        print("\n=== Database Creator ===")
        print("Welcome! This tool helps you create and manage SQLite databases.\n")
        
        # Show recent databases
        if recent_dbs:
            print("Recent databases:")
            for i, path in enumerate(recent_dbs):
                print(f"{i+1}. {path}")
            print("0. Create a new database")
            
            choice = input("\nSelect a database or 0 for new: ")
            
            if choice != "0":
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(recent_dbs):
                        db_path = recent_dbs[index]
                    else:
                        print("❌ Invalid choice.")
                except ValueError:
                    print("❌ Invalid input.")
        
        # Get path for new database
        if db_path is None:
            default_path = os.path.join(config.get("default_path", os.getcwd()), DEFAULT_DB_NAME)
            db_path = input(f"Enter database path [{default_path}]: ") or default_path
    
    # Create database manager
    db_manager = DatabaseManager(db_path)
    
    # Main menu loop
    while True:
        print(f"\n=== Database Creator Menu (DB: {db_manager.db_path}) ===")
        print("1. Set up database schema")
        print("2. Add customer")
        print("3. Add product")
        print("4. List products")
        print("5. Place order")
        print("6. List orders")
        print("7. Export database")
        print("8. Import database")
        print("9. Save current schema as template")
        print("0. Exit")
        
        choice = input("\nChoose an option: ")
        
        if choice == "1":
            setup_database(db_manager)
        elif choice == "2":
            add_customer(db_manager)
        elif choice == "3":
            add_product(db_manager)
        elif choice == "4":
            list_products(db_manager)
        elif choice == "5":
            place_order(db_manager)
        elif choice == "6":
            list_orders(db_manager)
        elif choice == "7":
            export_database(db_manager)
        elif choice == "8":
            import_database(db_manager)
        elif choice == "9":
            save_current_as_template(db_manager)
        elif choice == "0":
            print("\nThank you for using Database Creator!")
            break
        else:
            print("❌ Invalid choice. Try again.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database Creator - SQLite database manager")
    parser.add_argument("-d", "--database", help="Path to the database file")
    parser.add_argument("-t", "--template", help="Apply a template to initialize the database")
    parser.add_argument("--export", help="Export database to specified format (sql, json, csv)")
    parser.add_argument("--output", help="Output path for export")
    parser.add_argument("--gui", action="store_true", help="Launch in GUI mode (if available)")
    
    return parser.parse_args()

def command_line_interface():
    """Entry point for the command line interface."""
    args = parse_args()
    
    # Handle database path
    db_path = args.database
    
    # Create DatabaseManager
    db_manager = DatabaseManager(db_path) if db_path else None
    
    # Process command-line specific functions
    if args.template and db_manager:
        templates = DatabaseTemplates()
        if templates.apply_template(db_manager, args.template):
            print(f"✅ Applied template '{args.template}' to {db_manager.db_path}")
        else:
            print(f"❌ Failed to apply template '{args.template}'")
    elif args.export and db_manager:
        if args.output:
            if db_manager.export_database(args.export, args.output):
                print(f"✅ Exported to {args.output}")
            else:
                print("❌ Export failed")
        else:
            print("❌ Output path is required for export")
    elif args.gui:
        try:
            launch_gui(db_path)
        except ImportError:
            print("❌ GUI mode requires additional packages (tkinter).")
            print("Install with: pip install tk")
            menu(db_path)  # Fall back to CLI
    else:
        # Launch interactive menu
        menu(db_path)

def launch_gui(db_path=None):
    """Launch the GUI interface if tkinter is available."""
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        
        class DatabaseCreatorGUI:
            def __init__(self, root, db_path=None):
                self.root = root
                self.root.title("Database Creator")
                self.root.geometry("800x600")
                self.db_path = db_path
                self.db_manager = None
                
                # Set up the main frame
                self.main_frame = ttk.Frame(root, padding="10")
                self.main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Database selection
                self.setup_database_selector()
                
                # Content area
                self.content_frame = ttk.Frame(self.main_frame)
                self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
                
                # Status bar
                self.status_var = tk.StringVar()
                self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
                self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
                
                # Show welcome screen
                self.show_welcome()
                
                # Connect to database if path provided
                if db_path:
                    self.connect_database(db_path)
            
            def setup_database_selector(self):
                """Set up the database selection area."""
                frame = ttk.LabelFrame(self.main_frame, text="Database")
                frame.pack(fill=tk.X, pady=5)
                
                self.db_path_var = tk.StringVar()
                if self.db_path:
                    self.db_path_var.set(self.db_path)
                
                ttk.Label(frame, text="Database File:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                self.path_entry = ttk.Entry(frame, textvariable=self.db_path_var, width=50)
                self.path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
                
                ttk.Button(frame, text="Browse...", command=self.browse_database).grid(row=0, column=2, padx=5, pady=5)
                ttk.Button(frame, text="Connect", command=self.connect_to_entered_path).grid(row=0, column=3, padx=5, pady=5)
                
                frame.columnconfigure(1, weight=1)
            
            def browse_database(self):
                """Open file browser to select database."""
                config = load_config()
                initial_dir = config.get("default_path", os.getcwd())
                
                file_path = filedialog.asksaveasfilename(
                    initialdir=initial_dir,
                    title="Select Database File",
                    filetypes=(("SQLite Databases", "*.db"), ("All Files", "*.*")),
                    defaultextension=".db"
                )
                
                if file_path:
                    self.db_path_var.set(file_path)
            
            def connect_to_entered_path(self):
                """Connect to the database specified in the entry field."""
                path = self.db_path_var.get().strip()
                if path:
                    self.connect_database(path)
                else:
                    messagebox.showerror("Error", "Please specify a database file path")
            
            def connect_database(self, path):
                """Connect to the specified database."""
                try:
                    self.db_path = path
                    self.db_manager = DatabaseManager(path)
                    self.show_main_menu()
                    self.status_var.set(f"Connected to {path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to connect to database: {e}")
            
            def show_welcome(self):
                """Show the welcome screen."""
                # Clear content frame
                for widget in self.content_frame.winfo_children():
                    widget.destroy()
                
                ttk.Label(
                    self.content_frame, 
                    text="Welcome to Database Creator!",
                    font=("Arial", 16)
                ).pack(pady=20)
                
                ttk.Label(
                    self.content_frame,
                    text="Select or create a database to get started.",
                    font=("Arial", 12)
                ).pack(pady=10)
                
                # Recent databases
                config = load_config()
                recent_dbs = config.get("recent_databases", [])
                
                if recent_dbs:
                    ttk.Label(
                        self.content_frame,
                        text="Recent Databases:",
                        font=("Arial", 12, "bold")
                    ).pack(pady=(20, 5), anchor=tk.W)
                    
                    for db_path in recent_dbs:
                        frame = ttk.Frame(self.content_frame)
                        frame.pack(fill=tk.X, pady=2)
                        
                        ttk.Label(frame, text=db_path).pack(side=tk.LEFT, padx=10)
                        ttk.Button(
                            frame, text="Open", 
                            command=lambda p=db_path: self.connect_database(p)
                        ).pack(side=tk.RIGHT)
            
            def show_main_menu(self):
                """Show the main menu after connecting to a database."""
                # Clear content frame
                for widget in self.content_frame.winfo_children():
                    widget.destroy()
                
                # Create a frame for the buttons
                btn_frame = ttk.Frame(self.content_frame)
                btn_frame.pack(pady=20)
                
                # Define menu options
                options = [
                    ("Set Up Schema", self.setup_schema),
                    ("Customers", self.manage_customers),
                    ("Products", self.manage_products),
                    ("Orders", self.manage_orders),
                    ("Export Database", self.export_db),
                    ("Import Data", self.import_data),
                    ("Manage Templates", self.manage_templates)
                ]
                
                # Create buttons
                for i, (text, command) in enumerate(options):
                    ttk.Button(
                        btn_frame, text=text, command=command, width=20
                    ).grid(row=i//3, column=i%3, padx=10, pady=10)
            
            def setup_schema(self):
                """Show the schema setup screen."""
                # This would be expanded to show template selection and schema design UI
                # For now, just a placeholder
                messagebox.showinfo("Not Implemented", "Schema setup UI not yet implemented")
                
            def manage_customers(self):
                """Show the customer management screen."""
                messagebox.showinfo("Not Implemented", "Customer management UI not yet implemented")
                
            def manage_products(self):
                """Show the product management screen."""
                messagebox.showinfo("Not Implemented", "Product management UI not yet implemented")
                
            def manage_orders(self):
                """Show the order management screen."""
                messagebox.showinfo("Not Implemented", "Order management UI not yet implemented")
                
            def export_db(self):
                """Show the export database screen."""
                messagebox.showinfo("Not Implemented", "Export UI not yet implemented")
                
            def import_data(self):
                """Show the import data screen."""
                messagebox.showinfo("Not Implemented", "Import UI not yet implemented")
                
            def manage_templates(self):
                """Show the template management screen."""
                messagebox.showinfo("Not Implemented", "Template management UI not yet implemented")
        
        # Create and run the application
        root = tk.Tk()
        app = DatabaseCreatorGUI(root, db_path)
        root.mainloop()
        
    except ImportError:
        raise ImportError("Tkinter is required for GUI mode")

if __name__ == "__main__":
    command_line_interface()

# These functions are from the original file but are now integrated into the DatabaseManager class
# They are being removed to avoid conflicts with the new implementation

if __name__ == "__main__":
    command_line_interface()
