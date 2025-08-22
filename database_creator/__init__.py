"""
Database Creator Package
A modular SQLite database creation and management tool.
"""

__version__ = "1.0.0"

# Use lazy imports to avoid circular dependencies
# These functions provide access to the core functionality without circular imports
def get_database_manager():
    """Get the DatabaseManager class"""
    from .database import DatabaseManager
    return DatabaseManager

def get_templates():
    """Get the DatabaseTemplates class"""
    from .templates import DatabaseTemplates
    return DatabaseTemplates

def get_security():
    """Get security functions"""
    from .security import hash_password, verify_password, Validator
    return hash_password, verify_password, Validator

def get_advanced_templates():
    """Get advanced template functions"""
    from .advanced_templates import get_advanced_ecommerce_template
    return get_advanced_ecommerce_template

# Make DB_STORAGE_DIR available without causing circular imports
from .config import DB_STORAGE_DIR

__version__ = "1.0.0"
