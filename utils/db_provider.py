"""
Database provider interface for Academia Tokugawa.

This module provides a unified interface for database operations,
handling the switching between DynamoDB and SQLite implementations
with proper fallback mechanisms.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from enum import Enum, auto

logger = logging.getLogger('tokugawa_bot')

# Determine which database implementation to use
USE_DYNAMODB = os.environ.get('USE_DYNAMODB', 'false').lower() == 'true'

class DatabaseType(Enum):
    DYNAMODB = auto()
    SQLITE = auto()

class DatabaseProvider:
    _instance = None
    _current_db_type: Optional[DatabaseType] = None
    _dynamo_available: bool = False
    _sqlite_available: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseProvider, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the database provider and check availability of both databases."""
        if USE_DYNAMODB:
            try:
                # Try to import DynamoDB module
                from utils import dynamodb as dynamo_db
                self._dynamo_available = dynamo_db.init_db()
                if self._dynamo_available:
                    logger.info("DynamoDB is available")
                    self._current_db_type = DatabaseType.DYNAMODB
                    return  # Exit early if DynamoDB is successfully initialized
            except Exception as e:
                logger.warning(f"DynamoDB initialization failed: {e}")
                self._dynamo_available = False

        # Only initialize SQLite if DynamoDB is not enabled or failed
        if not USE_DYNAMODB:
            try:
                # Try to import SQLite module
                from utils import database as sqlite_db
                sqlite_db.init_db()
                self._sqlite_available = True
                logger.info("SQLite is available")
                self._current_db_type = DatabaseType.SQLITE
            except Exception as e:
                logger.error(f"SQLite initialization failed: {e}")
                self._sqlite_available = False

    @property
    def current_db_type(self) -> DatabaseType:
        """Get the current database type being used."""
        return self._current_db_type

    def get_db_implementation(self):
        """Get the current database implementation module."""
        if self._current_db_type == DatabaseType.DYNAMODB:
            from utils import dynamodb as db_impl
        else:
            from utils import database as db_impl
        return db_impl

    def sync_to_dynamo_if_empty(self) -> bool:
        """
        Sync data from SQLite to DynamoDB if DynamoDB is empty.
        Returns True if sync was successful or not needed, False otherwise.
        """
        if not self._dynamo_available:
            logger.warning("Cannot sync to DynamoDB: DynamoDB is not available")
            return False

        try:
            from utils import dynamodb as dynamo_db
            from utils import database as sqlite_db

            # Ensure DynamoDB is properly initialized first
            if not dynamo_db.init_db():
                logger.error("Failed to initialize DynamoDB before sync")
                return False

            # Check if DynamoDB is empty by querying a key table
            try:
                # Try to get a system flag as a test
                test_flag = dynamo_db.get_system_flag('test_flag')
                if test_flag is not None:
                    logger.info("DynamoDB is not empty, skipping sync")
                    return True
            except Exception as e:
                logger.error(f"Error checking DynamoDB emptiness: {e}")
                return False

            logger.info("DynamoDB appears to be empty, starting sync from SQLite")
            
            # Ensure SQLite is initialized
            if not sqlite_db.init_db():
                logger.error("Failed to initialize SQLite before sync")
                return False

            return True

        except Exception as e:
            logger.error(f"Error during sync to DynamoDB: {e}")
            return False

    def fallback_to_sqlite(self) -> bool:
        """
        Switch to SQLite as the database implementation.
        Returns True if successful, False otherwise.
        """
        if not self._sqlite_available:
            logger.error("Cannot fallback to SQLite: SQLite is not available")
            return False

        try:
            from utils import database as sqlite_db
            sqlite_db.init_db()
            self._current_db_type = DatabaseType.SQLITE
            logger.info("Successfully switched to SQLite")
            return True
        except Exception as e:
            logger.error(f"Error falling back to SQLite: {e}")
            return False

    def ensure_dynamo_available(self) -> bool:
        """
        Ensure DynamoDB is available and switch to it if possible.
        Returns True if DynamoDB is available, False otherwise.
        """
        if self._current_db_type == DatabaseType.DYNAMODB:
            return True

        try:
            from utils import dynamodb as dynamo_db
            if dynamo_db.init_db():
                self._current_db_type = DatabaseType.DYNAMODB
                self._dynamo_available = True
                logger.info("Successfully switched to DynamoDB")
                return True
        except Exception as e:
            logger.error(f"Error switching to DynamoDB: {e}")
            return False

        return False

# Create a singleton instance
db_provider = DatabaseProvider()

# Re-export all functions from the current implementation
def get_player(*args, **kwargs):
    return db_provider.get_db_implementation().get_player(*args, **kwargs)

def create_player(*args, **kwargs):
    return db_provider.get_db_implementation().create_player(*args, **kwargs)

def update_player(*args, **kwargs):
    return db_provider.get_db_implementation().update_player(*args, **kwargs)

def get_all_players(*args, **kwargs):
    return db_provider.get_db_implementation().get_all_players(*args, **kwargs)

def get_top_players(*args, **kwargs):
    return db_provider.get_db_implementation().get_top_players(*args, **kwargs)

def get_top_players_by_reputation(*args, **kwargs):
    return db_provider.get_db_implementation().get_top_players_by_reputation(*args, **kwargs)

def get_club(*args, **kwargs):
    return db_provider.get_db_implementation().get_club(*args, **kwargs)

def get_all_clubs(*args, **kwargs):
    return db_provider.get_db_implementation().get_all_clubs(*args, **kwargs)

def get_club_members(*args, **kwargs):
    return db_provider.get_db_implementation().get_club_members(*args, **kwargs)

def get_relevant_npcs(*args, **kwargs):
    return db_provider.get_db_implementation().get_relevant_npcs(*args, **kwargs)

def update_club_reputation_weekly(*args, **kwargs):
    return db_provider.get_db_implementation().update_club_reputation_weekly(*args, **kwargs)

def get_top_clubs_by_activity(*args, **kwargs):
    return db_provider.get_db_implementation().get_top_clubs_by_activity(*args, **kwargs)

def record_club_activity(*args, **kwargs):
    return db_provider.get_db_implementation().record_club_activity(*args, **kwargs)

def store_event(*args, **kwargs):
    return db_provider.get_db_implementation().store_event(*args, **kwargs)

def get_event(*args, **kwargs):
    return db_provider.get_db_implementation().get_event(*args, **kwargs)

def get_events_by_date(*args, **kwargs):
    return db_provider.get_db_implementation().get_events_by_date(*args, **kwargs)

def update_event_status(*args, **kwargs):
    return db_provider.get_db_implementation().update_event_status(*args, **kwargs) 