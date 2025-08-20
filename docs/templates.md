# Template Guide

This guide explains how to use and create database templates in the Database Creator application.

## Built-in Templates

The application comes with several built-in templates for common use cases:

### Simple Blog

A basic blog database structure:
- `posts`: Blog post entries
- `comments`: User comments on posts
- `categories`: Post categories
- `users`: User accounts

### Contact Manager

Manage personal or business contacts:
- `contacts`: Basic contact information
- `groups`: Contact grouping
- `interactions`: Record of communications
- `notes`: Additional information

### Task Tracker

Track tasks and projects:
- `tasks`: Individual tasks with status
- `projects`: Group tasks into projects
- `users`: Assigned users
- `statuses`: Custom status definitions

### Media Library

Catalog media collections:
- `media`: Media items (music, videos, books)
- `artists`: Creator information
- `genres`: Categorization
- `collections`: Custom groupings

### Web Store

Basic e-commerce functionality:
- `products`: Product information
- `customers`: Customer accounts
- `orders`: Purchase records
- `categories`: Product categorization

### Advanced E-Commerce

A comprehensive online store system with:
- `customers`: Customer accounts
- `products`: Product catalog
- `orders`: Order processing
- `inventory`: Stock management
- `shipping`: Shipping records
- `payments`: Payment processing
- `reviews`: Customer reviews
- And many more tables with proper relationships

### Project Management

Team collaboration tools:
- `projects`: Project information
- `tasks`: Tasks within projects
- `resources`: Team members and assets
- `timelines`: Project scheduling
- `documents`: Project documentation

## Creating Custom Templates

You can create your own custom templates to save time setting up similar databases.

### Template Format

Templates are defined as JSON structures with the following format:

```json
{
  "table_name": {
    "columns": {
      "column_name": "column_type_and_constraints",
      ...
    },
    "constraints": [
      "table_level_constraint1",
      ...
    ]
  },
  ...
}
```

For example:

```json
{
  "contacts": {
    "columns": {
      "contact_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
      "first_name": "TEXT NOT NULL",
      "last_name": "TEXT NOT NULL",
      "email": "TEXT UNIQUE",
      "phone": "TEXT",
      "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
  },
  "groups": {
    "columns": {
      "group_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
      "name": "TEXT NOT NULL",
      "description": "TEXT"
    }
  },
  "contact_groups": {
    "columns": {
      "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
      "contact_id": "INTEGER NOT NULL",
      "group_id": "INTEGER NOT NULL"
    },
    "constraints": [
      "FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)",
      "FOREIGN KEY (group_id) REFERENCES groups(group_id)"
    ]
  }
}
```

### Creating a Template Programmatically

You can create templates using the Python API:

```python
from database_creator.templates import DatabaseTemplates

# Initialize templates
templates = DatabaseTemplates()

# Define a custom template
custom_template = {
    "books": {
        "columns": {
            "book_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "title": "TEXT NOT NULL",
            "author": "TEXT NOT NULL",
            "isbn": "TEXT UNIQUE",
            "published_year": "INTEGER",
            "genre": "TEXT",
            "description": "TEXT"
        }
    },
    "readers": {
        "columns": {
            "reader_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE"
        }
    },
    "loans": {
        "columns": {
            "loan_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "book_id": "INTEGER NOT NULL",
            "reader_id": "INTEGER NOT NULL",
            "loan_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "return_date": "TIMESTAMP",
            "returned": "BOOLEAN DEFAULT 0"
        },
        "constraints": [
            "FOREIGN KEY (book_id) REFERENCES books(book_id)",
            "FOREIGN KEY (reader_id) REFERENCES readers(reader_id)"
        ]
    }
}

# Save the template
templates.save_template(
    name="library_manager",
    description="Library book management system",
    tables=custom_template
)
```

### Saving Templates via GUI

You can also save custom templates from the GUI:

1. Create the tables for your template in a database
2. Go to "Templates" → "Save as Template"
3. Enter a name and description for your template
4. Select the tables to include
5. Click "Save Template"

### Applying Templates

To apply a template to a database:

#### GUI Method:
1. Connect to a database
2. Go to "Templates" → "Apply Template"
3. Select your template from the list
4. Click "Apply"

#### CLI Method:
```bash
python main.py --db your_database.db apply-template template_name
```

#### Programmatic Method:
```python
from database_creator.database import DatabaseManager
from database_creator.templates import DatabaseTemplates

db_manager = DatabaseManager("your_database.db")
templates = DatabaseTemplates()
templates.apply_template(db_manager, "template_name")
```

## Advanced Template Features

### Template Customization

You can modify templates before applying them:

```python
template = templates.get_template("web_store")

# Add a new column to the customers table
template["customers"]["columns"]["loyalty_points"] = "INTEGER DEFAULT 0"

# Apply the modified template
templates.apply_template(db_manager, template)
```

### Template Inheritance

You can build templates that extend other templates:

```python
# Get base template
base_template = templates.get_template("web_store")

# Extend it
extended_template = base_template.copy()
extended_template["blog_posts"] = {
    "columns": {
        "post_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "title": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "author_id": "INTEGER NOT NULL",
        "published_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    },
    "constraints": [
        "FOREIGN KEY (author_id) REFERENCES customers(customer_id)"
    ]
}

# Save as a new template
templates.save_template(
    name="web_store_with_blog",
    description="Web store with integrated blog functionality",
    tables=extended_template
)
