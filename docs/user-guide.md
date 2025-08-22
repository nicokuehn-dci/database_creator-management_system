# Database Creator User Guide

This guide provides detailed instructions for using the Database Creator application.

## Table of Contents

- [Getting Started](#getting-started)
- [GUI Interface](#gui-interface)
- [CLI Interface](#cli-interface)
- [Working with Templates](#working-with-templates)
- [Import and Export](#import-and-export)
- [Security Features](#security-features)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/database-creator.git
   cd database-creator
   ```

2. Make sure you have Python 3.6 or higher installed.

### First Run

To start the application:

- For the graphical interface:
  ```bash
  python main.py --gui
  ```

- For the command line interface:
  ```bash
  python main.py --cli
  ```

## GUI Interface

The graphical interface provides an intuitive way to work with databases.

### Main Window

The main window is divided into several areas:
- Connection panel: Shows the current database connection
- Table list: Shows tables in the current database
- Notebook with tabs:
  - Databases tab: Browse and manage your database files
  - Schema tab: View and modify table structure
  - SQL Query tab: Execute SQL queries
  - Data tab: View and edit table data
  - Templates tab: Apply templates to the database

### Databases Tab

The Databases tab provides a central place to manage your database files:

1. **Create a New Database**:
   - Click "Create New Database" button
   - Enter a name for your database
   - The database will be saved in the designated storage folder

2. **Open an Existing Database**:
   - Browse databases in the storage folder on the left panel
   - Double-click any database to view its details and contents
   - Click "Open Selected Database" to work with that database
   
3. **Search and Sort Databases**:
   - Use the search box to filter databases by name
   - Sort by name, size, or modification date
   - Toggle between ascending and descending order
   
4. **Database Information**:
   - The right panel shows details about the selected database
   - View file size, modification date, and table count
   - Preview table contents with the table selector

5. **Table Data Management**:
   - Preview table data in the built-in viewer
   - Edit rows directly from the database tab
   - Add new rows or delete existing ones
   - Search within table data to find specific values
   
6. **Database Operations**:
   - Export database to SQL, CSV, or JSON formats
   - Clone databases to create backups or test versions
   - Delete unwanted databases with the "Delete Selected Database" button
   - Import databases from other locations
   - All databases are kept organized in a central storage folder

### Creating a Database

1. Click "File" → "New Database" or use the Databases tab
2. Choose a location and name for your database file
3. The application will create and connect to the new database

### Creating Tables

#### Standard Method

1. Click "Edit" → "Create Table"
2. Enter a table name
3. Add columns with their types and constraints
4. Click "Create" to create the table

#### Excel-like Interface

1. Click "Edit" → "Create Table (Excel-like)" or click the "Excel Table" button
2. Enter a table name at the top
3. Use the spreadsheet-like interface to define your table:
   - Columns are added horizontally with data type selection menus
   - Add constraints like PK (Primary Key), NN (Not Null), and UQ (Unique)
   - View the SQL preview at the bottom to see the CREATE TABLE statement
4. Click "Create Table" to create the table

### Editing Data with Excel-like Interface

1. Right-click on a table in the table list
2. Select "Edit Data (Excel-like)"
3. Use the spreadsheet interface to:
   - Add rows using the "Add Row" button
   - Delete rows by selecting them and clicking "Delete Selected"
   - Edit cell values by double-clicking on a cell
4. Click "Save Changes" when finished

The Excel-like interface provides a familiar spreadsheet experience that makes database creation and editing more intuitive, especially for users who are more comfortable with spreadsheet applications than SQL commands.

### Running Queries

1. Switch to the "SQL Query" tab
2. Enter your SQL query in the text area
3. Click "Execute Query" to run the query
4. Results will be displayed in the results area

## CLI Interface

The command line interface provides powerful scripting capabilities.

### Basic Commands

- Create a database:
  ```bash
  python main.py --db new_database.db
  ```

- Apply a template:
  ```bash
  python main.py --db mydb.db apply-template web_store
  ```

- Create a table:
  ```bash
  python main.py --db mydb.db create users --columns "id INTEGER PRIMARY KEY" "username TEXT UNIQUE NOT NULL" "password TEXT NOT NULL"
  ```

- Insert data:
  ```bash
  python main.py --db mydb.db insert users --values "username:john_doe" "password:hashed_password_here"
  ```

- Query data:
  ```bash
  python main.py --db mydb.db query "SELECT * FROM users"
  ```

### Batch Operations

You can chain operations together:

```bash
python main.py --db new_project.db apply-template task_tracker query "SELECT * FROM tasks"
```

## Working with Templates

Templates provide predefined database structures for common applications.

### Using Built-in Templates

1. Connect to a database
2. Go to "Templates" → "Apply Template" (GUI) or use `apply-template` command (CLI)
3. Select a template from the list
4. Confirm to create the tables

### Available Templates

- **Simple Blog**: Basic blog structure (posts, comments, users)
- **Contact Manager**: Personal or business contacts
- **Task Tracker**: Project management and task tracking
- **Media Library**: Music, video, or book collection
- **Web Store**: Basic e-commerce functionality
- **Advanced E-Commerce**: Comprehensive online store system
- **Project Management**: Team collaboration tools

## Import and Export

### Exporting Data

You can export your database in several formats:

- SQL (complete schema and data):
  ```bash
  python main.py --db mydb.db --export mydb.sql
  ```

- In GUI mode:
  - For the entire database: "File" → "Export" → "SQL"
  - For a specific table: "File" → "Export" → "CSV"

### Importing Data

#### Importing SQL

To import a previously exported database:

- From SQL file:
  ```bash
  python main.py --db new_db.db --import backup.sql
  ```

- In GUI mode, use "File" → "Import" → "SQL"

#### Importing CSV/Text Files

The application includes a powerful text file import wizard:

1. Connect to a database
2. Go to "File" → "Import" → "CSV/Text File"
3. Follow the wizard steps:
   - **Step 1: Select File**
     - Choose file type (CSV, TSV, plain text)
     - Browse for your file
     - Set table name and encoding
   
   - **Step 2: Preview Data**
     - Choose delimiter character (comma, tab, custom)
     - Specify if first row contains headers
     - Preview how the data will be interpreted
   
   - **Step 3: Map Columns**
     - Map file columns to database columns
     - Set data types (TEXT, INTEGER, etc.)
     - Add constraints (PRIMARY KEY, NOT NULL, UNIQUE)
     - Choose which columns to include/exclude
   
   - **Step 4: Import**
     - Choose how to handle existing tables (replace or append)
     - Set batch size for large imports
     - Execute the import process with progress tracking

#### Importing Excel Files

To import data from Excel spreadsheets:

1. Connect to a database
2. Go to "File" → "Import" → "Excel File"
3. Select your Excel file
4. Choose which sheet to import
5. The data will be imported into a new table with the same name as the sheet

## Security Features

### Password Hashing

The database creator includes secure password hashing for user authentication:

```python
from database_creator.security import hash_password, verify_password

# Hash a password
hashed_password, salt = hash_password("user_password")

# Verify a password
is_valid = verify_password(hashed_password, "provided_password")
```

## Troubleshooting

### Common Issues

- **Connection Error**: Make sure the database file exists and is not locked by another process
- **Import Error**: Ensure the import file is in a valid format
- **Template Application Error**: Check if the database already has tables with the same names

### Getting Help

If you encounter any issues:

1. Check the troubleshooting section in this guide
2. Look for similar issues in the project's GitHub Issues
3. Create a new issue with detailed information about your problem
