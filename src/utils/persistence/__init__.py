"""
Persistence module for Academia Tokugawa.

This module provides database access and persistence functionality.
"""

from utils.persistence.db_provider import db_provider
from utils.persistence.dynamodb import init_db

__all__ = [
    'db_provider',
    'init_db'
]
