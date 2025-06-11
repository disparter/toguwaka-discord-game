"""
Database interface for Academia Tokugawa.

This module serves as the main interface for database operations,
re-exporting functions from the persistence modules.
"""

from utils.persistence.db_provider import (
    get_player,
    update_player,
    get_club,
    store_cooldown,
    get_player_inventory,
    add_item_to_inventory,
    get_cooldowns,
    clear_expired_cooldowns,
    init_db,
    db_provider,
    store_event,
    get_event,
    get_story_progress,
    update_story_progress,
    get_market_items,
    add_market_item,
    get_quiz_questions,
    add_quiz_question,
    get_player_grades,
    update_player_grade
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
    'init_db',
    'db_provider',
    'store_event',
    'get_event',
    'get_story_progress',
    'update_story_progress',
    'get_market_items',
    'add_market_item',
    'get_quiz_questions',
    'add_quiz_question',
    'get_player_grades',
    'update_player_grade'
]
