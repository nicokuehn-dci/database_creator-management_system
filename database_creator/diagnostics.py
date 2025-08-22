"""
Diagnostics module for the Database Creator application.
Provides utilities for troubleshooting, system information, and health checks.
"""
import sys
import os
import platform
import sqlite3
import importlib
import subprocess
from typing import Dict, List, Any, Optional, Tuple

def get_system_info() -> Dict[str, str]:
    """Get system information for diagnostics."""
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "os": platform.system(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "sqlite_version": sqlite3.sqlite_version,
    }
    return info

def check_database_health(db_path: str) -> Dict[str, Any]:
    """Check the health of a SQLite database file."""
    if not os.path.exists(db_path):
        return {"status": "error", "message": f"Database file not found: {db_path}"}

    try:
        # Check if the database is valid
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get basic database info
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]

        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]

        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]

        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        # Calculate size
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)

        conn.close()

        return {
            "status": "ok",
            "file_exists": True,
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2),
            "page_count": page_count,
            "page_size": page_size,
            "integrity": integrity,
            "table_count": len(tables),
            "tables": tables,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_package_versions() -> Dict[str, str]:
    """Check versions of installed required packages."""
    required_packages = [
        "openpyxl",
        "pymysql",
        "psycopg2",
        "pyodbc",
        "requests",
        "pandas",
        "matplotlib",
        "numpy",
        "seaborn"
    ]

    versions = {}
    for pkg in required_packages:
        try:
            module = importlib.import_module(pkg)
            version = getattr(module, "__version__", "Unknown")
            versions[pkg] = version
        except ImportError:
            versions[pkg] = "Not installed"

    return versions

def repair_database(db_path: str) -> Dict[str, Any]:
    """Attempt to repair a corrupted SQLite database."""
    if not os.path.exists(db_path):
        return {"status": "error", "message": f"Database file not found: {db_path}"}

    try:
        # Create a backup first
        backup_path = f"{db_path}.backup"
        import shutil
        shutil.copy2(db_path, backup_path)

        # Try to dump and reload the database
        dump_path = f"{db_path}.dump"
        with open(dump_path, "w") as f:
            subprocess.run(
                ["sqlite3", db_path, ".dump"],
                stdout=f,
                text=True,
                check=True
            )

        # Create a new database from the dump
        fixed_path = f"{db_path}.fixed"
        if os.path.exists(fixed_path):
            os.remove(fixed_path)

        subprocess.run(
            ["sqlite3", fixed_path, f".read {dump_path}"],
            text=True,
            check=True
        )

        # Verify the new database
        health = check_database_health(fixed_path)
        if health["status"] == "ok" and health["integrity"] == "ok":
            # Replace the original with the fixed version
            os.replace(fixed_path, db_path)
            os.remove(dump_path)
            return {
                "status": "success",
                "message": "Database successfully repaired",
                "backup_path": backup_path
            }
        else:
            return {
                "status": "error",
                "message": "Repair attempt failed, integrity check failed",
                "backup_path": backup_path,
                "dump_path": dump_path,
                "fixed_path": fixed_path
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_diagnostic() -> Dict[str, Any]:
    """Run a comprehensive diagnostic on the system and database environment."""
    from .config import load_config, DB_STORAGE_DIR, CONFIG_FILE

    diagnostic = {
        "system_info": get_system_info(),
        "package_versions": check_package_versions(),
        "config_exists": os.path.exists(CONFIG_FILE),
        "config_path": CONFIG_FILE,
        "storage_dir_exists": os.path.exists(DB_STORAGE_DIR),
    }

    # Check config
    try:
        config = load_config()
        diagnostic["config_valid"] = True
        diagnostic["config_keys"] = list(config.keys())
    except Exception as e:
        diagnostic["config_valid"] = False
        diagnostic["config_error"] = str(e)

    # Check databases directory
    if diagnostic["storage_dir_exists"]:
        db_files = [f for f in os.listdir(DB_STORAGE_DIR) if f.endswith('.db')]
        diagnostic["database_count"] = len(db_files)
        diagnostic["databases"] = db_files

    return diagnostic
