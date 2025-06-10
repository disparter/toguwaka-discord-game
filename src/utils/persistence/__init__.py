"""
Persistence module for Academia Tokugawa.

This module provides database access and persistence functionality.
"""

from utils.persistence.db_provider import (
    db_provider,
    init_db
)

from utils.persistence.dynamodb_players import (
    get_player,
    create_player,
    update_player
)

from utils.persistence.dynamodb_clubs import (
    get_all_clubs,
    get_club
)

from utils.persistence.dynamodb import (
    get_player_inventory,
    add_item_to_inventory,
    remove_item_from_inventory,
    get_system_flag
)

__all__ = [
    'db_provider',
    'init_db',
    'get_player',
    'create_player',
    'update_player',
    'get_player_inventory',
    'add_item_to_inventory',
    'remove_item_from_inventory',
    'get_all_clubs',
    'get_club',
    'get_system_flag'
]
