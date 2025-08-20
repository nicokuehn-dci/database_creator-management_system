"""
Configuration management for database creator.
"""

import os
import json

# Constants
DEFAULT_DB_NAME = "database.db"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".database_creator")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TEMPLATES_DIR = os.path.join(CONFIG_DIR, "templates")

# Define database storage directory
# First try to use a 'databases' folder in the application directory
APP_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_STORAGE_DIR = os.path.join(APP_DIR, "databases")
if not os.path.exists(DB_STORAGE_DIR):
    # Fall back to the config directory if we can't write to the app directory
    DB_STORAGE_DIR = os.path.join(CONFIG_DIR, "databases")

# Create configuration and database directories if they don't exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(DB_STORAGE_DIR, exist_ok=True)

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
    """Load configuration from file or create default if none exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Config file corrupted. Using default configuration.")
            return DEFAULT_CONFIG
    else:
        # Create default config
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG

# Save configuration
def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        
def ensure_directory_exists(directory_path):
    """Ensure that the specified directory exists."""
    os.makedirs(directory_path, exist_ok=True)
    return os.path.exists(directory_path)
