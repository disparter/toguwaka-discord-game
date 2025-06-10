"""
Database interface for Academia Tokugawa.

This module serves as the main interface for database operations,
re-exporting functions from the persistence modules.
"""

import os
from src.utils.persistence.db_provider import (
    get_player,
    update_player,
    get_club,
    store_cooldown,
    get_player_inventory,
    add_item_to_inventory,
    get_cooldowns,
    clear_expired_cooldowns,
    init_db
)

# Re-export all database functions
__all__ = [
    'get_player',
    'update_player',
    'get_club',
    'store_cooldown',
    'get_player_inventory',
    'add_item_to_inventory',
    'get_cooldowns',
    'clear_expired_cooldowns',
    'init_db'
] 