"""
Database Creator Package
A modular SQLite database creation and management tool.
"""

# Import main modules
from .database import DatabaseManager
from .config import load_config, save_config
from .templates import DatabaseTemplates
from .security import hash_password, verify_password, Validator
from .advanced_templates import get_advanced_ecommerce_template
from .excel_gui import ExcelTableCreator, ExcelDataEditor
from .db_connections import DatabaseConnection, DatabaseUtils
from .db_management import DatabaseManagementTab, create_databases_tab
from .analytics import create_analytics_tab

__version__ = "1.0.0"
