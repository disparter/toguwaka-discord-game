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
from utils.persistence.dynamodb_market import (
    get_market_items as _get_market_items,
    add_market_item as _add_market_item
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
            # Scan the players table and sort by reputation
            response = self.PLAYERS_TABLE.scan(
                ProjectionExpression='PK, SK, #n, reputation, #l, exp',
                ExpressionAttributeNames={
                    '#n': 'name',
                    '#l': 'level'
                }
            )
            
            # Filter and sort players
            players = []
            for item in response.get('Items', []):
                if item.get('PK', '').startswith('PLAYER#'):
                    players.append({
                        'user_id': item['PK'].split('#')[1],
                        'name': item.get('name', 'Unknown'),
                        'reputation': item.get('reputation', 0),
                        'level': item.get('level', 1),
                        'exp': item.get('exp', 0)
                    })
            
            # Sort by reputation in descending order
            players.sort(key=lambda x: x.get('reputation', 0), reverse=True)
            
            # Return top N players
            return players[:limit]
        except Exception as e:
            logger.error(f"Error getting top players by reputation: {e}")
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

    # --- Market operations ---
    async def get_market_items(self) -> List[Dict[str, Any]]:
        """Get all items in the market."""
        return await _get_market_items()

    async def add_market_item(self, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Add an item to the market."""
        return await _add_market_item(item_id, item_data)

    # --- Event operations ---
    async def store_event(self, event_id: str, name: str, description: str, event_type: str,
                         channel_id: str, message_id: str, start_time: datetime,
                         end_time: datetime, participants: List[str], data: Dict[str, Any],
                         completed: bool = False) -> bool:
        """Store an event in database."""
        try:
            self.EVENTS_TABLE.put_item(
                Item={
                    'PK': f'EVENT#{event_id}',
                    'SK': 'INFO',
                    'name': name,
                    'description': description,
                    'type': event_type,
                    'channel_id': channel_id,
                    'message_id': message_id,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'participants': participants,
                    'data': data,
                    'completed': completed
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error storing event: {e}")
            return False

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event from database."""
        try:
            response = self.EVENTS_TABLE.get_item(
                Key={
                    'PK': f'EVENT#{event_id}',
                    'SK': 'INFO'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting event: {e}")
            return None

    async def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events from database."""
        try:
            response = self.EVENTS_TABLE.scan()
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all events: {e}")
            return []

    async def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all active events from database."""
        try:
            current_time = datetime.now().isoformat()
            response = self.EVENTS_TABLE.scan(
                FilterExpression='start_time <= :now AND end_time > :now AND completed = :completed',
                ExpressionAttributeValues={
                    ':now': current_time,
                    ':completed': False
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting active events: {e}")
            return []

    # --- Item operations ---
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item from database."""
        try:
            response = self.ITEMS_TABLE.get_item(
                Key={
                    'PK': f'ITEM#{item_id}',
                    'SK': 'INFO'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting item: {e}")
            return None

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items from database."""
        try:
            response = self.ITEMS_TABLE.scan()
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all items: {e}")
            return []

    # --- Quiz operations ---
    async def get_quiz_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a quiz question from database."""
        try:
            response = self.QUIZ_QUESTIONS_TABLE.get_item(
                Key={
                    'PK': f'QUESTION#{question_id}',
                    'SK': 'INFO'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting quiz question: {e}")
            return None

    async def get_all_quiz_questions(self) -> List[Dict[str, Any]]:
        """Get all quiz questions from database."""
        try:
            response = self.QUIZ_QUESTIONS_TABLE.scan()
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all quiz questions: {e}")
            return []

    async def get_quiz_answers(self, question_id: str) -> List[Dict[str, Any]]:
        """Get all answers for a quiz question."""
        try:
            response = self.QUIZ_ANSWERS_TABLE.scan(
                FilterExpression='question_id = :qid',
                ExpressionAttributeValues={
                    ':qid': question_id
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting quiz answers: {e}")
            return []

    async def add_quiz_question(self, question_id: str, question_data: Dict[str, Any]) -> bool:
        """Add a new quiz question."""
        try:
            self.QUIZ_QUESTIONS_TABLE.put_item(
                Item={
                    'PK': f'QUESTION#{question_id}',
                    'SK': 'INFO',
                    **question_data
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error adding quiz question: {e}")
            return False

    # --- Grade operations ---
    async def get_player_grades(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """Get all grades for a player."""
        try:
            response = self.GRADES_TABLE.scan(
                FilterExpression='user_id = :uid',
                ExpressionAttributeValues={
                    ':uid': user_id
                }
            )
            return response.get('Items', {})
        except Exception as e:
            logger.error(f"Error getting player grades: {e}")
            return {}

    async def update_player_grade(self, user_id: str, subject: str, grade: float) -> bool:
        """Update a player's grade."""
        try:
            self.GRADES_TABLE.put_item(
                Item={
                    'PK': f'GRADE#{user_id}',
                    'SK': f'SUBJECT#{subject}',
                    'grade': grade,
                    'timestamp': datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error updating player grade: {e}")
            return False

    async def get_monthly_average_grades(self, user_id: str) -> Dict[str, float]:
        """Get monthly average grades for a player."""
        try:
            response = self.GRADES_TABLE.scan(
                FilterExpression='user_id = :uid',
                ExpressionAttributeValues={
                    ':uid': user_id
                }
            )
            
            # Calculate averages
            grades = response.get('Items', [])
            averages = {}
            for grade in grades:
                subject = grade['SK'].split('#')[1]
                if subject not in averages:
                    averages[subject] = []
                averages[subject].append(grade['grade'])
            
            # Calculate final averages
            for subject in averages:
                averages[subject] = sum(averages[subject]) / len(averages[subject])
            
            return averages
        except Exception as e:
            logger.error(f"Error getting monthly average grades: {e}")
            return {}

    # --- Vote operations ---
    async def add_vote(self, vote_id: str, voter_id: str, candidate_id: str) -> bool:
        """Add a vote to database."""
        try:
            self.VOTES_TABLE.put_item(
                Item={
                    'PK': f'VOTE#{vote_id}',
                    'SK': f'VOTER#{voter_id}',
                    'candidate_id': candidate_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error adding vote: {e}")
            return False

    async def get_vote_results(self, vote_id: str) -> Dict[str, int]:
        """Get results for a vote."""
        try:
            response = self.VOTES_TABLE.scan(
                FilterExpression='PK = :vid',
                ExpressionAttributeValues={
                    ':vid': f'VOTE#{vote_id}'
                }
            )
            
            # Count votes
            results = {}
            for vote in response.get('Items', []):
                candidate_id = vote['candidate_id']
                results[candidate_id] = results.get(candidate_id, 0) + 1
            
            return results
        except Exception as e:
            logger.error(f"Error getting vote results: {e}")
            return {}

    # --- Reputation operations ---
    async def update_player_reputation(self, user_id: str, amount: int) -> bool:
        """Update a player's reputation."""
        try:
            # Get current player data
            player = await self.get_player(user_id)
            if not player:
                return False
            
            # Update reputation
            player['reputation'] = player.get('reputation', 0) + amount
            await self.update_player(user_id, **player)
            return True
        except Exception as e:
            logger.error(f"Error updating player reputation: {e}")
            return False

    # --- Story operations ---
    async def get_story_progress(self, user_id: str) -> Dict[str, Any]:
        """Get a player's story progress."""
        try:
            response = self.MAIN_TABLE.get_item(
                Key={
                    'PK': f'STORY#{user_id}',
                    'SK': 'PROGRESS'
                }
            )
            return response.get('Item', {})
        except Exception as e:
            logger.error(f"Error getting story progress: {e}")
            return {}

    async def update_story_progress(self, user_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update a player's story progress."""
        try:
            self.MAIN_TABLE.put_item(
                Item={
                    'PK': f'STORY#{user_id}',
                    'SK': 'PROGRESS',
                    **progress_data
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error updating story progress: {e}")
            return False

    # --- System operations ---
    async def get_system_flag(self, flag_name: str) -> Optional[str]:
        """Get a system flag value."""
        try:
            response = self.SYSTEM_FLAGS_TABLE.get_item(
                Key={
                    'PK': f'FLAG#{flag_name}',
                    'SK': 'VALUE'
                }
            )
            return response.get('Item', {}).get('value')
        except Exception as e:
            logger.error(f"Error getting system flag: {e}")
            return None

    async def set_system_flag(self, flag_name: str, value: str, flag_type: str = 'system') -> bool:
        """Set a system flag value."""
        try:
            self.SYSTEM_FLAGS_TABLE.put_item(
                Item={
                    'PK': f'FLAG#{flag_name}',
                    'SK': 'VALUE',
                    'value': value,
                    'type': flag_type,
                    'timestamp': datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error setting system flag: {e}")
            return False

    async def get_daily_events_flags(self) -> List[Dict[str, Any]]:
        """Get all daily events flags."""
        try:
            response = self.SYSTEM_FLAGS_TABLE.scan(
                FilterExpression='type = :type',
                ExpressionAttributeValues={
                    ':type': 'daily_event'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting daily events flags: {e}")
            return []

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
    """Get player data asynchronously."""
    try:
        table = db_provider.PLAYERS_TABLE
        response = await table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            }
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting player data: {e}")
        return None

def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(get_player_async(user_id), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout waiting for get_player")
            return None
    else:
        return loop.run_until_complete(get_player_async(user_id))

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

def get_cooldowns(user_id: str) -> Dict[str, datetime]:
    """Get all cooldowns for a user."""
    return _get_cooldowns(user_id)

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

def get_top_players_by_reputation(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top players by reputation (sync version)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(db_provider.get_top_players_by_reputation(limit), loop)
        try:
            # Add a timeout of 5 seconds to prevent deadlock
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            logger.error("Timeout waiting for get_top_players_by_reputation")
            return []
    else:
        return loop.run_until_complete(db_provider.get_top_players_by_reputation(limit))

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
