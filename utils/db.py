"""
Database compatibility layer for Academia Tokugawa.

This module provides a unified interface for database operations,
allowing the application to switch between SQLite and DynamoDB
implementations without changing the code that uses the database.

Usage:
    from utils.db import get_player, update_player, ...

Configuration:
    Set the USE_DYNAMODB environment variable to 'true' to use DynamoDB,
    or 'false' to use SQLite (default).
"""

import os
import logging

logger = logging.getLogger('tokugawa_bot')

# Determine which database implementation to use
USE_DYNAMODB = os.environ.get('USE_DYNAMODB', 'false').lower() == 'true'
logger.info(f"Database configuration - USE_DYNAMODB: {USE_DYNAMODB}")

if USE_DYNAMODB:
    logger.info("Using DynamoDB database implementation")
    try:
        from utils import dynamodb as db_impl
        logger.info("Successfully imported DynamoDB implementation")
    except ImportError as e:
        logger.error(f"Error importing DynamoDB module: {e}")
        logger.warning("Falling back to SQLite database implementation")
        from utils import database as db_impl
else:
    logger.info("Using SQLite database implementation")
    from utils import database as db_impl

# Re-export all functions from the selected implementation
# Player operations
get_player = db_impl.get_player
create_player = db_impl.create_player
update_player = db_impl.update_player
get_all_players = db_impl.get_all_players
get_top_players = db_impl.get_top_players
get_top_players_by_reputation = db_impl.get_top_players_by_reputation

# Club operations
get_club = db_impl.get_club
get_all_clubs = db_impl.get_all_clubs
get_club_members = db_impl.get_club_members
get_relevant_npcs = db_impl.get_relevant_npcs
update_club_reputation_weekly = db_impl.update_club_reputation_weekly
get_top_clubs_by_activity = db_impl.get_top_clubs_by_activity
record_club_activity = db_impl.record_club_activity

# Event operations
store_event = db_impl.store_event
get_event = db_impl.get_event
get_events_by_date = db_impl.get_events_by_date
update_event_status = db_impl.update_event_status
get_active_events = db_impl.get_active_events

# Cooldown operations
store_cooldown = db_impl.store_cooldown
get_cooldowns = db_impl.get_cooldowns
clear_expired_cooldowns = db_impl.clear_expired_cooldowns

# System flag operations
get_system_flag = db_impl.get_system_flag
set_system_flag = db_impl.set_system_flag

# Grade operations
get_player_grades = db_impl.get_player_grades
update_player_grade = db_impl.update_player_grade
get_monthly_average_grades = db_impl.get_monthly_average_grades

# Voting operations
add_vote = db_impl.add_vote
get_vote_results = db_impl.get_vote_results
update_player_reputation = db_impl.update_player_reputation

# Quiz operations
get_quiz_questions = db_impl.get_quiz_questions
record_quiz_answer = db_impl.record_quiz_answer

# Initialize the database
init_db = db_impl.init_db

# Call init_db to ensure the database is initialized
init_db()

# Add logging to track function calls
def log_db_call(func_name):
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
        result = func_name(*args, **kwargs)
        logger.info(f"{func_name} returned: {result}")
        return result
    return wrapper

# Wrap all exported functions with logging
for name in dir(db_impl):
    if not name.startswith('_'):
        func = getattr(db_impl, name)
        if callable(func):
            setattr(db_impl, name, log_db_call(func))