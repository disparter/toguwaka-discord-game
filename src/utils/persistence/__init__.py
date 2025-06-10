"""
Persistence module for Academia Tokugawa.

This module provides database access and persistence functionality.
"""

from src.utils.persistence.db_provider import db_provider
from src.utils.persistence.dynamodb import init_db
from src.utils.persistence.dynamo_migration import normalize_player_data

__all__ = [
    'db_provider',
    'init_db',
    'normalize_player_data'
] 