"""
Security-related functions for password hashing and validation.
"""

import hashlib
import secrets
import re
from typing import Tuple, Union

# Secure hash function for passwords
def hash_password(password: str, salt: bytes = None) -> Tuple[str, bytes]:
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

class Validator:
    """Utilities for validating user input."""

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
