"""
Database provider for Academia Tokugawa.

Este módulo é a ÚNICA interface pública para acesso ao banco de dados.
Ele usa exclusivamente DynamoDB para todas as operações.
"""

import os
import logging
import asyncio
import concurrent.futures
from typing import Any, Dict, List, Optional
from datetime import datetime
import boto3
from decimal import Decimal
import json
from botocore.exceptions import ClientError

# Import all database operations with aliases to avoid circular dependencies
from utils.persistence.dynamodb_players import (
    get_player as _get_player,
    create_player as _create_player,
    update_player as _update_player,
    get_all_players as _get_all_players,
    get_top_players as _get_top_players
)
from utils.persistence.dynamodb_clubs import (
    get_club as _get_club,
    get_all_clubs as _get_all_clubs,
    get_club_members as _get_club_members
)
from utils.persistence.dynamodb_cooldowns import (
    store_cooldown as _store_cooldown,
    get_cooldowns as _get_cooldowns,
    get_cooldown as _get_cooldown,
    clear_expired_cooldowns as _clear_expired_cooldowns
)
from utils.persistence.dynamodb_inventory import (
    get_player_inventory as _get_player_inventory,
    add_item_to_inventory as _add_item_to_inventory,
    remove_item_from_inventory as _remove_item_from_inventory
)
from utils.persistence.dynamodb_events import (
    store_event as _store_event,
    get_event as _get_event,
    get_all_events as _get_all_events,
    get_active_events as _get_active_events
)
from utils.persistence.dynamodb_items import (
    get_item as _get_item,
    get_all_items as _get_all_items
)
from utils.persistence.dynamodb_quiz import (
    get_quiz_question as _get_quiz_question,
    get_all_quiz_questions as _get_all_quiz_questions,
    get_quiz_answers as _get_quiz_answers,
    add_quiz_question as _add_quiz_question
)
from utils.persistence.dynamodb_grades import (
    get_player_grades as _get_player_grades,
    update_player_grade as _update_player_grade,
    get_monthly_average_grades as _get_monthly_average_grades
)
from utils.persistence.dynamodb_votes import (
    add_vote as _add_vote,
    get_vote_results as _get_vote_results
)
from utils.persistence.dynamodb_reputation import (
    update_player_reputation as _update_player_reputation
)
from utils.persistence.dynamodb_story import (
    get_story_progress as _get_story_progress,
    update_story_progress as _update_story_progress
)
from utils.persistence.dynamodb_system import (
    get_system_flag as _get_system_flag,
    set_system_flag as _set_system_flag,
    get_daily_events_flags as _get_daily_events_flags
)
from utils.persistence.dynamodb_market import (
    get_market_items as _get_market_items,
    add_market_item as _add_market_item
)
from utils.persistence.dynamodb_scheduled_events import (
    create_scheduled_event as _create_scheduled_event,
    get_scheduled_event as _get_scheduled_event,
    get_upcoming_events as _get_upcoming_events,
    get_active_events as _get_active_scheduled_events
)

logger = logging.getLogger('tokugawa_bot')

class DBProvider:
    """Database provider class that encapsulates all database operations."""

    def __init__(self):
        # Configurar região padrão para o DynamoDB
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.AWS_REGION)
        
        # Initialize all tables
        self.PLAYERS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_PLAYERS_TABLE', 'Jogadores'))
        self.INVENTORY_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_INVENTORY_TABLE', 'Inventario'))
        self.CLUBS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_CLUBS_TABLE', 'Clubes'))
        self.EVENTS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_EVENTS_TABLE', 'Eventos'))
        self.COOLDOWNS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_COOLDOWNS_TABLE', 'Cooldowns'))
        self.GRADES_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_GRADES_TABLE', 'Notas'))
        self.MARKET_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_MARKET_TABLE', 'Mercado'))
        self.ITEMS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_ITEMS_TABLE', 'Itens'))
        self.CLUB_ACTIVITIES_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_CLUB_ACTIVITIES_TABLE', 'ClubActivities'))
        self.QUIZ_QUESTIONS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_QUIZ_QUESTIONS_TABLE', 'QuizQuestions'))
        self.QUIZ_ANSWERS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_QUIZ_ANSWERS_TABLE', 'QuizAnswers'))
        self.SYSTEM_FLAGS_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_SYSTEM_FLAGS_TABLE', 'SystemFlags'))
        self.VOTES_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_VOTES_TABLE', 'Votos'))
        self.MAIN_TABLE = self.dynamodb.Table(os.getenv('DYNAMODB_TABLE', 'AcademiaTokugawa'))
        
        self.initialize_tables()

    def initialize_tables(self):
        """Initialize DynamoDB tables."""
        try:
            # Check if all tables exist and are accessible
            tables = [
                self.PLAYERS_TABLE,
                self.INVENTORY_TABLE,
                self.CLUBS_TABLE,
                self.EVENTS_TABLE,
                self.COOLDOWNS_TABLE,
                self.GRADES_TABLE,
                self.MARKET_TABLE,
                self.ITEMS_TABLE,
                self.CLUB_ACTIVITIES_TABLE,
                self.QUIZ_QUESTIONS_TABLE,
                self.QUIZ_ANSWERS_TABLE,
                self.SYSTEM_FLAGS_TABLE,
                self.VOTES_TABLE,
                self.MAIN_TABLE
            ]
            
            for table in tables:
                table.table_status
                
            logger.info("All DynamoDB tables initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing tables: {e}")
            raise

    def ensure_dynamo_available(self) -> bool:
        """Check if DynamoDB is available and all required tables exist."""
        try:
            # List of required tables
            required_tables = [
                self.PLAYERS_TABLE,
                self.INVENTORY_TABLE,
                self.CLUBS_TABLE,
                self.EVENTS_TABLE,
                self.COOLDOWNS_TABLE,
                self.GRADES_TABLE,
                self.MARKET_TABLE,
                self.ITEMS_TABLE,
                self.CLUB_ACTIVITIES_TABLE,
                self.QUIZ_QUESTIONS_TABLE,
                self.QUIZ_ANSWERS_TABLE,
                self.SYSTEM_FLAGS_TABLE,
                self.VOTES_TABLE,
                self.MAIN_TABLE
            ]
            
            # Check each table
            for table in required_tables:
                try:
                    # Try to describe the table
                    table.table_status
                    logger.info(f"Table {table.name} is available")
                except Exception as e:
                    logger.error(f"Table {table.name} is not available: {e}")
                    return False
            
            logger.info("All required DynamoDB tables are available")
            return True
        except Exception as e:
            logger.error(f"Error checking DynamoDB availability: {e}")
            return False

    async def sync_to_dynamo_if_empty(self) -> bool:
        """Check if DynamoDB tables are empty and sync data if needed."""
        try:
            # Check if players table is empty
            response = self.PLAYERS_TABLE.scan(Limit=1)
            if not response.get('Items'):
                logger.info("Players table is empty, no sync needed")
                return True
            return True
        except Exception as e:
            logger.error(f"Error checking DynamoDB tables: {e}")
            return False

    # --- Player operations ---
    async def get_player(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get player data from database."""
        return await _get_player(user_id)

    async def create_player(self, user_id: str, name: str, **kwargs) -> bool:
        """Create a new player in database."""
        return await _create_player(user_id, name, **kwargs)

    async def update_player(self, user_id: str, **kwargs) -> bool:
        """Update player data in database."""
        return await _update_player(user_id, **kwargs)

    async def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players from database."""
        return await _get_all_players()

    async def get_top_players(self, limit: int = 10) -> list:
        """Get top players by level."""
        return await _get_top_players(limit)

    async def get_top_players_by_reputation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by reputation."""
        try:
            table = self.PLAYERS_TABLE
            response = await table.scan(
                Limit=limit,
                ScanIndexForward=False,  # Sort in descending order
                ProjectionExpression='PK, name, reputation, level, exp'
            )
            
            players = []
            for item in response.get('Items', []):
                player = {
                    'user_id': item['PK'].replace('PLAYER#', ''),
                    'name': item.get('name', 'Unknown'),
                    'reputation': item.get('reputation', 0),
                    'level': item.get('level', 1),
                    'exp': item.get('exp', 0)
                }
                players.append(player)
            
            return players
        except Exception as e:
            logger.error(f"Error getting top players by reputation: {str(e)}")
            return []

    # --- Club operations ---
    async def get_club(self, club_id) -> Optional[Dict[str, Any]]:
        """Get club data from database."""
        return await _get_club(club_id)

    async def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs from database."""
        return await _get_all_clubs()

    async def get_club_members(self, club_id: str) -> list:
        """Get all members of a club."""
        return await _get_club_members(club_id)

    # --- Cooldown operations ---
    async def store_cooldown(self, user_id: str, command: str, expiry_time: datetime) -> bool:
        """Store a cooldown in database."""
        return await _store_cooldown(user_id, command, expiry_time)

    async def get_cooldowns(self, user_id: str) -> Dict[str, datetime]:
        """Get all cooldowns for a user."""
        return await _get_cooldowns(user_id)

    async def get_cooldown(self, user_id: str, command: str) -> Optional[datetime]:
        """Get a specific cooldown for a user."""
        return await _get_cooldown(user_id, command)

    async def clear_expired_cooldowns(self, user_id: Optional[str] = None) -> int:
        """Clear expired cooldowns."""
        return await _clear_expired_cooldowns(user_id)

    # --- Inventory operations ---
    async def get_player_inventory(self, user_id: str) -> Dict[str, Any]:
        """Get player inventory from database."""
        return await _get_player_inventory(user_id)

    async def add_item_to_inventory(self, user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Add an item to player inventory."""
        return await _add_item_to_inventory(user_id, item_id, item_data)

    async def remove_item_from_inventory(self, user_id: str, item_id: str) -> bool:
        """Remove an item from player inventory."""
        return await _remove_item_from_inventory(user_id, item_id)

    # --- Event operations ---
    async def store_event(self, event_id: str, name: str, description: str, event_type: str,
                         channel_id: str, message_id: str, start_time: datetime,
                         end_time: datetime, participants: List[str], data: Dict[str, Any],
                         completed: bool = False) -> bool:
        """Store an event in database."""
        return await _store_event(event_id, name, description, event_type, channel_id, message_id,
                               start_time, end_time, participants, data, completed)

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event from database."""
        return await _get_event(event_id)

    async def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events from database."""
        return await _get_all_events()

    async def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all active events from database."""
        return await _get_active_events()

    # --- Item operations ---
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item from database."""
        return await _get_item(item_id)

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items from database."""
        return await _get_all_items()

    # --- Quiz operations ---
    async def get_quiz_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a quiz question from database."""
        return await _get_quiz_question(question_id)

    async def get_all_quiz_questions(self) -> List[Dict[str, Any]]:
        """Get all quiz questions from database."""
        return await _get_all_quiz_questions()

    async def get_quiz_answers(self, question_id: str) -> List[Dict[str, Any]]:
        """Get all answers for a quiz question."""
        return await _get_quiz_answers(question_id)

    async def add_quiz_question(self, question_id: str, question_data: Dict[str, Any]) -> bool:
        """Add a new quiz question."""
        return await _add_quiz_question(question_id, question_data)

    # --- Grade operations ---
    async def get_player_grades(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """Get all grades for a player."""
        return await _get_player_grades(user_id)

    async def update_player_grade(self, user_id: str, subject: str, grade: float) -> bool:
        """Update a player's grade."""
        return await _update_player_grade(user_id, subject, grade)

    async def get_monthly_average_grades(self, user_id: str) -> Dict[str, float]:
        """Get monthly average grades for a player."""
        return await _get_monthly_average_grades(user_id)

    # --- Vote operations ---
    async def add_vote(self, vote_id: str, voter_id: str, candidate_id: str) -> bool:
        """Add a vote to database."""
        return await _add_vote(vote_id, voter_id, candidate_id)

    async def get_vote_results(self, vote_id: str) -> Dict[str, int]:
        """Get results for a vote."""
        return await _get_vote_results(vote_id)

    # --- Reputation operations ---
    async def update_player_reputation(self, user_id: str, amount: int) -> bool:
        """Update a player's reputation."""
        return await _update_player_reputation(user_id, amount)

    # --- Story operations ---
    async def get_story_progress(self, user_id: str) -> Dict[str, Any]:
        """Get a player's story progress."""
        return await _get_story_progress(user_id)

    async def update_story_progress(self, user_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update a player's story progress."""
        return await _update_story_progress(user_id, progress_data)

    # --- System operations ---
    async def get_system_flag(self, flag_name: str) -> Optional[str]:
        """Get a system flag value."""
        return await _get_system_flag(flag_name)

    async def set_system_flag(self, flag_name: str, value: str, flag_type: str = 'system') -> bool:
        """Set a system flag value."""
        return await _set_system_flag(flag_name, value, flag_type)

    async def get_daily_events_flags(self) -> List[Dict[str, Any]]:
        """Get all daily events flags."""
        return await _get_daily_events_flags()

    # --- Market operations ---
    async def get_market_items(self) -> List[Dict[str, Any]]:
        """Get all items in the market."""
        return await _get_market_items()

    async def add_market_item(self, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Add an item to the market."""
        return await _add_market_item(item_id, item_data)

    # --- Scheduled events operations ---
    async def create_scheduled_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """Create a new scheduled event."""
        return await _create_scheduled_event(event_id, event_data)

    async def get_scheduled_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a scheduled event."""
        return await _get_scheduled_event(event_id)

    async def get_upcoming_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming scheduled events."""
        return await _get_upcoming_events(limit)

    async def get_active_scheduled_events(self) -> List[Dict[str, Any]]:
        """Get currently active scheduled events."""
        return await _get_active_scheduled_events()

    # --- Database initialization ---
    async def init_db(self) -> bool:
        """Initialize database with required tables and data."""
        try:
            if not self.ensure_dynamo_available():
                logger.error("DynamoDB is not available")
                return False

            if not await self.sync_to_dynamo_if_empty():
                logger.error("Failed to sync data to DynamoDB")
                return False

            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

# Create a singleton instance of DBProvider
db_provider = DBProvider()

# Create wrapper functions for all methods that need to be exported
async def get_player_async(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from database (async version)."""
    return await db_provider.get_player(user_id)

def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run the async function in the event loop
    if loop.is_running():
        # If we're already in an event loop, use run_coroutine_threadsafe
        future = asyncio.run_coroutine_threadsafe(db_provider.get_player(user_id), loop)
        try:
            # First attempt with 10 second timeout
            return future.result(timeout=10)
        except concurrent.futures.TimeoutError:
            logger.warning(f"First timeout waiting for get_player({user_id}), retrying...")
            # Second attempt with 20 second timeout
            try:
                future = asyncio.run_coroutine_threadsafe(db_provider.get_player(user_id), loop)
                return future.result(timeout=20)
            except concurrent.futures.TimeoutError:
                logger.error(f"Second timeout waiting for get_player({user_id}), final attempt...")
                # Final attempt with 30 second timeout
                try:
                    future = asyncio.run_coroutine_threadsafe(db_provider.get_player(user_id), loop)
                    return future.result(timeout=30)
                except concurrent.futures.TimeoutError:
                    logger.error(f"Final timeout waiting for get_player({user_id})")
                    return None
    else:
        # Otherwise, use run_until_complete
        return loop.run_until_complete(db_provider.get_player(user_id))

async def update_player_async(user_id: str, **kwargs) -> bool:
    """Update player data in database (async version)."""
    return await db_provider.update_player(user_id, **kwargs)

def update_player(user_id: str, **kwargs) -> bool:
    """Update player data in database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.update_player(user_id, **kwargs), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for update_player({user_id})")
            return False
    else:
        return loop.run_until_complete(db_provider.update_player(user_id, **kwargs))

async def get_club_async(club_id) -> Optional[Dict[str, Any]]:
    """Get club data from database (async version)."""
    return await db_provider.get_club(club_id)

def get_club(club_id) -> Optional[Dict[str, Any]]:
    """Get club data from database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.get_club(club_id), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for get_club({club_id})")
            return None
    else:
        return loop.run_until_complete(db_provider.get_club(club_id))

async def store_cooldown_async(user_id: str, command: str, expiry_time: datetime) -> bool:
    """Store command cooldown in database (async version)."""
    return await db_provider.store_cooldown(user_id, command, expiry_time)

def store_cooldown(user_id: str, command: str, expiry_time: datetime) -> bool:
    """Store command cooldown in database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.store_cooldown(user_id, command, expiry_time), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for store_cooldown({user_id}, {command})")
            return False
    else:
        return loop.run_until_complete(db_provider.store_cooldown(user_id, command, expiry_time))

async def get_player_inventory_async(user_id: str) -> Dict[str, Any]:
    """Get a player's inventory (async version)."""
    return await db_provider.get_player_inventory(user_id)

def get_player_inventory(user_id: str) -> Dict[str, Any]:
    """Get a player's inventory (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.get_player_inventory(user_id), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for get_player_inventory({user_id})")
            return {}
    else:
        return loop.run_until_complete(db_provider.get_player_inventory(user_id))

async def add_item_to_inventory_async(user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add an item to a player's inventory (async version)."""
    return await db_provider.add_item_to_inventory(user_id, item_id, item_data)

def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add an item to a player's inventory (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.add_item_to_inventory(user_id, item_id, item_data), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for add_item_to_inventory({user_id}, {item_id})")
            return False
    else:
        return loop.run_until_complete(db_provider.add_item_to_inventory(user_id, item_id, item_data))

async def get_cooldowns_async(*args, **kwargs) -> List[Dict[str, Any]]:
    """Get all cooldowns (async version)."""
    return await db_provider.get_cooldowns(*args, **kwargs)

async def get_cooldown_async(user_id: str, command: str) -> Optional[datetime]:
    """Get cooldown for a specific command (async version)."""
    return await db_provider.get_cooldown(user_id, command)

def get_cooldowns(*args, **kwargs) -> List[Dict[str, Any]]:
    """Get all cooldowns (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.get_cooldowns(*args, **kwargs), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout waiting for get_cooldowns")
            return []
    else:
        return loop.run_until_complete(db_provider.get_cooldowns(*args, **kwargs))

def get_cooldown(user_id: str, command: str) -> Optional[datetime]:
    """Get cooldown for a specific command (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.get_cooldown(user_id, command), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout waiting for get_cooldown")
            return None
    else:
        return loop.run_until_complete(db_provider.get_cooldown(user_id, command))

async def clear_expired_cooldowns_async() -> int:
    """Clear expired cooldowns from database (async version)."""
    return await db_provider.clear_expired_cooldowns()

def clear_expired_cooldowns() -> int:
    """Clear expired cooldowns from database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.clear_expired_cooldowns(), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout waiting for clear_expired_cooldowns")
            return 0
    else:
        return loop.run_until_complete(db_provider.clear_expired_cooldowns())

async def init_db_async() -> bool:
    """Initialize the database (async version)."""
    return await db_provider.init_db()

def init_db() -> bool:
    """Initialize the database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.init_db(), loop)
        try:
            # Add a timeout of 10 seconds to prevent deadlock
            return future.result(timeout=10)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout waiting for database initialization")
            return False
    else:
        return loop.run_until_complete(db_provider.init_db())

async def get_top_players_async(limit: int = 10) -> list:
    """Get top players by level (async version)."""
    return await db_provider.get_top_players(limit)

def get_top_players(limit: int = 10) -> list:
    """Get top players by level (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.get_top_players(limit), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for get_top_players({limit})")
            return []
    else:
        return loop.run_until_complete(db_provider.get_top_players(limit))

async def store_event_async(event_id: str, name: str, description: str, event_type: str, 
                     channel_id: str, message_id: str, start_time: datetime, 
                     end_time: datetime, participants: List[str], data: Dict[str, Any], 
                     completed: bool = False) -> bool:
    """Store event data in database (async version)."""
    return await db_provider.store_event(event_id, name, description, event_type, 
                                        channel_id, message_id, start_time, 
                                        end_time, participants, data, completed)

def store_event(event_id: str, name: str, description: str, event_type: str, 
               channel_id: str, message_id: str, start_time: datetime, 
               end_time: datetime, participants: List[str], data: Dict[str, Any], 
               completed: bool = False) -> bool:
    """Store event data in database (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            db_provider.store_event(event_id, name, description, event_type, 
                                   channel_id, message_id, start_time, 
                                   end_time, participants, data, completed), 
            loop
        )
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for store_event({event_id})")
            return False
    else:
        return loop.run_until_complete(
            db_provider.store_event(event_id, name, description, event_type, 
                                   channel_id, message_id, start_time, 
                                   end_time, participants, data, completed)
        )

# Export the singleton instance and all wrapper functions
__all__ = [
    'db_provider',
    'get_player',
    'update_player',
    'get_club',
    'store_cooldown',
    'get_player_inventory',
    'add_item_to_inventory',
    'get_cooldowns',
    'get_cooldown',
    'clear_expired_cooldowns',
    'init_db',
    'get_player_async',
    'update_player_async',
    'get_club_async',
    'store_cooldown_async',
    'get_player_inventory_async',
    'add_item_to_inventory_async',
    'get_cooldowns_async',
    'get_cooldown_async',
    'clear_expired_cooldowns_async',
    'init_db_async',
    'get_top_players',
    'get_top_players_by_reputation',
    'get_top_players_async',
    'store_event',
    'store_event_async'
]
