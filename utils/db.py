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
from typing import List, Dict, Any
from utils.dynamodb import get_table, TABLES

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
# get_all_players = db_impl.get_all_players  # Removed because not implemented in dynamodb
# get_top_players = db_impl.get_top_players  # Not implemented in dynamodb
# get_top_players_by_reputation = db_impl.get_top_players_by_reputation  # Not implemented in dynamodb

# Club operations
async def get_clubs() -> List[Dict[str, Any]]:
    """Get all clubs from the database."""
    try:
        logger.info("Attempting to get clubs from database")
        if USE_DYNAMODB:
            logger.info("Using DynamoDB for club retrieval")
            clubs = await get_dynamodb_clubs()
            logger.info(f"Retrieved {len(clubs)} clubs from DynamoDB")
            if not clubs:
                logger.warning("No clubs retrieved from DynamoDB")
            return clubs
        else:
            logger.info("Using SQLite for club retrieval")
            async with get_db() as db:
                clubs = await db.fetch("SELECT * FROM clubs ORDER BY name")
                logger.info(f"Retrieved {len(clubs)} clubs from SQLite")
                if not clubs:
                    logger.warning("No clubs retrieved from SQLite")
                return [dict(club) for club in clubs]
    except Exception as e:
        logger.error(f"Error getting clubs: {e}")
        return []

async def get_dynamodb_clubs() -> List[Dict[str, Any]]:
    """Get all clubs from DynamoDB."""
    try:
        logger.info("Attempting to scan clubs table")
        table = get_table(TABLES['clubs'])
        logger.info(f"Got table reference: {table}")
        response = table.scan()
        logger.info(f"Raw DynamoDB response: {response}")
        clubs = []
        if 'Items' in response:
            logger.info(f"Found {len(response['Items'])} items in response")
            for item in response['Items']:
                logger.info(f"Processing club item: {item}")
                club = {
                    'club_id': item['NomeClube'],
                    'name': item['NomeClube'],
                    'description': item['descricao'],
                    'leader_id': item.get('lider_id', ''),
                    'reputacao': item.get('reputacao', 0)
                }
                logger.info(f"Converted club object: {club}")
                clubs.append(club)
        else:
            logger.warning("No 'Items' found in DynamoDB response")
        clubs.sort(key=lambda x: x['name'])
        logger.info(f"Final sorted clubs list: {clubs}")
        return clubs
    except Exception as e:
        logger.error(f"Error getting clubs from DynamoDB: {e}")
        return []

async def update_user_club(user_id: str, club_name: str) -> bool:
    """Update a user's club."""
    try:
        logger.info(f"Attempting to update user {user_id} to club {club_name}")
        if USE_DYNAMODB:
            logger.info("Using DynamoDB for club update")
            success = await update_dynamodb_user_club(user_id, club_name)
            logger.info(f"Club update result: {success}")
            return success
        else:
            logger.info("Using SQLite for club update")
            async with get_db() as db:
                success = await db.execute(
                    "UPDATE players SET club_id = ? WHERE user_id = ?",
                    (club_name, user_id)
                )
                logger.info(f"Club update result: {success}")
                return success
    except Exception as e:
        logger.error(f"Error updating user club: {e}")
        return False

async def update_dynamodb_user_club(user_id: str, club_name: str) -> bool:
    """Update a user's club in DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        logger.info(f"Updating user {user_id} to club {club_name}")
        
        response = await table.update_item(
            Key={
                'PK': f"PLAYER#{user_id}",
                'SK': 'PROFILE'
            },
            UpdateExpression='SET club_id = :club',
            ExpressionAttributeValues={
                ':club': club_name
            },
            ReturnValues='UPDATED_NEW'
        )
        
        logger.info(f"DynamoDB update response: {response}")
        return True
    except Exception as e:
        logger.error(f"Error updating user club in DynamoDB: {e}")
        return False

get_club = db_impl.get_club
get_all_clubs = db_impl.get_all_clubs
# get_club_members = db_impl.get_club_members  # Not implemented in dynamodb
# get_relevant_npcs = db_impl.get_relevant_npcs  # Not implemented in dynamodb
# update_club_reputation_weekly = db_impl.update_club_reputation_weekly  # Not implemented in dynamodb
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