"""
Template management for database schemas.
"""

import os
import json
import re
import datetime
from typing import Dict, List, Optional, Any

from .config import TEMPLATES_DIR


class DatabaseTemplates:
    """Manages database templates for quick setup."""
    
    def __init__(self, templates_dir=TEMPLATES_DIR):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        
        # Load built-in templates
        self.templates = get_default_templates()
    
    def list_templates(self) -> List[Dict]:
        """List all available templates."""
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_path = os.path.join(self.templates_dir, filename)
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    templates.append(template)
                except json.JSONDecodeError:
                    pass  # Skip invalid templates
        return templates
    
    def save_template(self, name: str, description: str, tables: Dict) -> str:
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
        
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        return template_path
    
    def load_template(self, template_name: str) -> Optional[Dict]:
        """Load a template by name."""
        filename = f"{template_name.lower().replace(' ', '_')}.json"
        template_path = os.path.join(self.templates_dir, filename)
        
        if not os.path.exists(template_path):
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name from built-in or saved templates."""
        # Check built-in templates first
        if template_name in self.templates:
            return self.templates[template_name]
        
        # Then check saved templates
        return self.load_template(template_name)
    
    def get_template_names(self) -> List[str]:
        """Get a list of all template names."""
        template_names = list(self.templates.keys())
        
        # Add saved templates
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_name = filename[:-5].replace('_', ' ')
                template_names.append(template_name)
        
        return sorted(template_names)
    
    def add_template(self, name: str, template_data: Dict[str, Any]) -> None:
        """Add a template to the built-in templates."""
        self.templates[name] = template_data

    def apply_template(self, db_manager, template_name: str) -> bool:
        """Apply a template to a database."""
        template = self.get_template(template_name)
        if not template:
            print(f"❌ Template '{template_name}' not found.")
            return False
        
        for table_name, table_def in template.items():
            columns = table_def['columns']
            constraints = table_def.get('constraints', [])
            
            # Format columns for create_table
            column_defs = [f"{name} {dtype}" for name, dtype in columns.items()]
            
            # Add any additional constraints
            if constraints:
                column_defs.extend(constraints)
            
            # Create the table
            db_manager.create_table(table_name, column_defs)
        
        return True


def get_default_templates() -> Dict:
    """Return dictionary of default templates."""
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
    
    # Return all templates
    return {
        "Web Store": {
            "description": "A complete e-commerce database with customers, products, orders, and line items",
            "tables": web_store
        },
        "Music Library": {
            "description": "A music collection database with artists, albums, songs, and playlists",
            "tables": music_library
        },
        "Task Manager": {
            "description": "A project management database with users, projects, tasks, and comments",
            "tables": task_manager
        },
        "Blog System": {
            "description": "A blogging database with users, posts, comments, categories, and tags",
            "tables": blog_system
        }
    }


def initialize_default_templates():
    """Initialize templates with defaults if empty."""
    templates = DatabaseTemplates()
    
    # If no templates exist, create defaults
    if not os.listdir(TEMPLATES_DIR):
        default_templates = get_default_templates()
        
        for name, template_data in default_templates.items():
            templates.save_template(
                name,
                template_data["description"],
                template_data["tables"]
            )
