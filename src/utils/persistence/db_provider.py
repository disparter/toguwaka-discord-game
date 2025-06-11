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

from utils.config import DYNAMODB_PLAYERS_TABLE, DYNAMODB_INVENTORY_TABLE, DYNAMODB_CLUBS_TABLE, DYNAMODB_TABLE

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
        try:
            response = self.PLAYERS_TABLE.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting player {user_id}: {str(e)}")
            return None

    async def create_player(self, user_id: str, name: str, **kwargs) -> bool:
        """Create a new player in database."""
        try:
            player_data = {
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE',
                'name': name,
                'level': 1,
                'exp': 0,
                'tusd': 1000,
                'club_id': None,
                'dexterity': 10,
                'intellect': 10,
                'charisma': 10,
                'power_stat': 10,
                'reputation': 0,
                'hp': 100,
                'max_hp': 100,
                'strength_level': 1,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                **kwargs
            }
            self.PLAYERS_TABLE.put_item(Item=player_data)
            return True
        except Exception as e:
            logger.error(f"Error creating player {user_id}: {str(e)}")
            return False

    async def update_player(self, user_id: str, **kwargs) -> bool:
        """Update player data in database."""
        try:
            # Get current player data
            current_player = await self.get_player(user_id)
            if not current_player:
                return False

            # Update fields
            update_expr = "SET "
            expr_attr_values = {}
            expr_attr_names = {}

            for key, value in kwargs.items():
                if key in current_player or key in ['level', 'exp', 'tusd', 'club_id', 'dexterity', 'intellect', 'charisma', 'power_stat', 'reputation', 'hp', 'max_hp', 'strength_level', 'story_progress']:
                    # Special handling for story_progress to ensure it's serialized
                    if key == 'story_progress' and isinstance(value, dict):
                        # Convert any non-serializable objects to their string representation
                        serialized_progress = {}
                        for k, v in value.items():
                            if isinstance(v, (list, dict)):
                                serialized_progress[k] = v
                            else:
                                serialized_progress[k] = str(v)
                        value = serialized_progress
                    
                    update_expr += f"#{key} = :{key}, "
                    expr_attr_values[f":{key}"] = value
                    expr_attr_names[f"#{key}"] = key

            # Always update last_active
            update_expr += "#last_active = :last_active"
            expr_attr_values[":last_active"] = datetime.now().isoformat()
            expr_attr_names["#last_active"] = "last_active"

            self.PLAYERS_TABLE.update_item(
                Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_attr_values,
                ExpressionAttributeNames=expr_attr_names
            )
            return True
        except Exception as e:
            logger.error(f"Error updating player {user_id}: {str(e)}")
            return False

    async def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players from DynamoDB."""
        try:
            response = self.PLAYERS_TABLE.scan()
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all players: {str(e)}")
            return []

    # --- Club operations ---
    async def get_club(self, club_id) -> Optional[Dict[str, Any]]:
        """Get club data from database."""
        try:
            # Ensure club_id is a string and properly formatted
            club_id_str = str(club_id)
            if not club_id_str.startswith('CLUB#'):
                club_id_str = f'CLUB#{club_id_str}'
            
            response = self.CLUBS_TABLE.get_item(Key={'PK': club_id_str, 'SK': 'INFO'})
            club_data = response.get('Item')
            if club_data:
                # Ensure required fields exist
                if 'name' not in club_data:
                    club_data['name'] = f"Club {club_id_str.replace('CLUB#', '')}"
                if 'description' not in club_data:
                    club_data['description'] = "No description available"
                if 'members' not in club_data:
                    club_data['members'] = []
                if 'reputation' not in club_data:
                    club_data['reputation'] = 0
            return club_data
        except Exception as e:
            logger.error(f"Error getting club {club_id}: {str(e)}")
            # Return a default club object with minimal required fields
            return {
                'PK': club_id_str,
                'SK': 'INFO',
                'name': f"Club {club_id_str.replace('CLUB#', '')}",
                'description': "No description available",
                'members': [],
                'reputation': 0
            }

    async def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs from database."""
        try:
            response = self.CLUBS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': 'CLUB#',
                    ':sk': 'INFO'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all clubs: {str(e)}")
            return []

    # --- Event operations ---
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event data from database."""
        try:
            response = self.EVENTS_TABLE.get_item(
                Key={
                    'PK': f'EVENT#{event_id}',
                    'SK': 'EVENT'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting event {event_id}: {str(e)}")
            return None

    async def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events from database."""
        try:
            response = self.EVENTS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': 'EVENT#',
                    ':sk': 'EVENT'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all events: {str(e)}")
            return []

    async def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all active (non-completed) events from database."""
        try:
            current_time = datetime.now().isoformat()
            response = self.EVENTS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk AND #completed = :completed AND #end_time > :current_time',
                ExpressionAttributeValues={
                    ':pk': 'EVENT#',
                    ':sk': 'EVENT',
                    ':completed': False,
                    ':current_time': current_time
                },
                ExpressionAttributeNames={
                    '#completed': 'completed',
                    '#end_time': 'end_time'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting active events: {str(e)}")
            return []

    async def clear_expired_cooldowns(self) -> int:
        """Clear all expired cooldowns from the database.
        
        Returns:
            int: Number of cooldowns cleared
        """
        try:
            current_time = datetime.now().isoformat()
            response = self.COOLDOWNS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk AND #expiry_time < :current_time',
                ExpressionAttributeValues={
                    ':pk': 'PLAYER#',
                    ':sk': 'COMMAND#',
                    ':current_time': current_time
                },
                ExpressionAttributeNames={
                    '#expiry_time': 'expiry_time'
                }
            )
            
            expired_cooldowns = response.get('Items', [])
            cleared_count = 0
            
            for cooldown in expired_cooldowns:
                try:
                    self.COOLDOWNS_TABLE.delete_item(
                        Key={
                            'PK': cooldown['PK'],
                            'SK': cooldown['SK']
                        }
                    )
                    cleared_count += 1
                except Exception as e:
                    logger.error(f"Error deleting expired cooldown: {str(e)}")
                    continue
            
            return cleared_count
        except Exception as e:
            logger.error(f"Error clearing expired cooldowns: {str(e)}")
            return 0

    # --- Item operations ---
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item data from database."""
        try:
            response = self.MAIN_TABLE.get_item(
                Key={
                    'PK': f'ITENS#{item_id}',
                    'SK': 'ITENS'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {str(e)}")
            return None

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items from database."""
        try:
            response = self.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': 'ITENS#',
                    ':sk': 'ITENS'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all items: {str(e)}")
            return []

    # --- Quiz operations ---
    async def get_quiz_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get quiz question data from database."""
        try:
            response = self.QUIZ_QUESTIONS_TABLE.get_item(
                Key={
                    'PK': f'QUIZ#{question_id}',
                    'SK': 'QUESTION'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting quiz question {question_id}: {str(e)}")
            return None

    async def get_all_quiz_questions(self) -> List[Dict[str, Any]]:
        """Get all quiz questions from database."""
        try:
            response = self.QUIZ_QUESTIONS_TABLE.scan(
                FilterExpression='begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':sk': 'QUESTION#'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all quiz questions: {str(e)}")
            return []

    async def get_quiz_answers(self, question_id: str) -> List[Dict[str, Any]]:
        """Get all answers for a quiz question from database."""
        try:
            response = self.QUIZ_ANSWERS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': 'QUIZANSWER#',
                    ':sk': f'QUESTION#{question_id}'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting quiz answers for question {question_id}: {str(e)}")
            return []

    # --- Cooldown operations ---
    async def store_cooldown(self, user_id: str, command: str, expiry_time: datetime) -> bool:
        """Store a cooldown for a command."""
        try:
            self.COOLDOWNS_TABLE.put_item(Item={
                'PK': f'PLAYER#{user_id}',
                'SK': f'COMMAND#{command}',
                'expiry_time': expiry_time.isoformat(),
                'command': command,
                'created_at': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error storing cooldown for player {user_id}: {str(e)}")
            return False

    async def get_cooldowns(self, user_id: str) -> Dict[str, datetime]:
        """Get all cooldowns for a player."""
        try:
            response = self.COOLDOWNS_TABLE.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'PLAYER#{user_id}'
                }
            )
            
            cooldowns = {}
            for item in response.get('Items', []):
                command = item['SK'].replace('COMMAND#', '')
                expiry_time = datetime.fromisoformat(item['expiry_time'])
                cooldowns[command] = expiry_time
                
            return cooldowns
        except Exception as e:
            logger.error(f"Error getting cooldowns for player {user_id}: {str(e)}")
            return {}

    async def clear_expired_cooldowns(self, user_id: str) -> bool:
        """Clear expired cooldowns for a player."""
        try:
            now = datetime.now()
            cooldowns = await self.get_cooldowns(user_id)
            
            for command, expiry_time in cooldowns.items():
                if expiry_time < now:
                    self.COOLDOWNS_TABLE.delete_item(
                        Key={
                            'PK': f'PLAYER#{user_id}',
                            'SK': f'COMMAND#{command}'
                        }
                    )
            return True
        except Exception as e:
            logger.error(f"Error clearing expired cooldowns for player {user_id}: {str(e)}")
            return False

    # --- Story operations ---
    async def get_story_progress(self, user_id: str) -> Dict[str, Any]:
        """Get player's story progress."""
        try:
            response = self.MAIN_TABLE.get_item(
                Key={
                    'PK': f'PLAYER#{user_id}',
                    'SK': 'STORY_PROGRESS'
                }
            )
            return response.get('Item', {})
        except Exception as e:
            logger.error(f"Error getting story progress for player {user_id}: {str(e)}")
            return {}

    async def update_story_progress(self, user_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update player's story progress."""
        try:
            self.MAIN_TABLE.put_item(Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'STORY_PROGRESS',
                **progress_data,
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error updating story progress for player {user_id}: {str(e)}")
            return False

    # --- Event operations ---
    async def store_event(self, event_id: str, name: str, description: str, event_type: str,
                         channel_id: str, message_id: str, start_time: datetime,
                         end_time: datetime, participants: List[str], data: Dict[str, Any],
                         completed: bool = False) -> bool:
        """Store an event in the database."""
        try:
            self.EVENTS_TABLE.put_item(Item={
                'PK': f'EVENT#{event_id}',
                'SK': f'TYPE#{event_type}',
                'name': name,
                'description': description,
                'channel_id': channel_id,
                'message_id': message_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'participants': participants,
                'data': data,
                'completed': completed,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error storing event {event_id}: {str(e)}")
            return False

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event by ID."""
        try:
            response = self.EVENTS_TABLE.get_item(
                Key={
                    'PK': f'EVENT#{event_id}',
                    'SK': 'EVENT'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting event {event_id}: {str(e)}")
            return None

    # --- Market operations ---
    async def get_market_items(self) -> List[Dict[str, Any]]:
        """Get all items in the market."""
        try:
            response = self.MARKET_TABLE.scan()
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting market items: {str(e)}")
            return []

    async def add_market_item(self, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Add an item to the market."""
        try:
            self.MARKET_TABLE.put_item(Item={
                'PK': f'ITEM#{item_id}',
                'SK': 'MARKET',
                **item_data,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding market item {item_id}: {str(e)}")
            return False

    # --- Quiz operations ---
    async def add_quiz_question(self, question_id: str, question_data: Dict[str, Any]) -> bool:
        """Add a quiz question."""
        try:
            self.QUIZ_QUESTIONS_TABLE.put_item(Item={
                'PK': f'QUIZ#{question_id}',
                'SK': 'QUESTION',
                **question_data,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding quiz question {question_id}: {str(e)}")
            return False

    # --- Grade operations ---
    async def get_player_grades(self, user_id: str) -> Dict[str, Dict[str, float]]:
        """Get all grades for a player."""
        try:
            response = self.GRADES_TABLE.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'GRADES'})
            return response.get('Item', {}).get('grades', {})
        except Exception as e:
            logger.error(f"Error getting grades for player {user_id}: {str(e)}")
            return {}

    async def update_player_grade(self, user_id: str, subject: str, grade: float) -> bool:
        """Update a player's grade for a subject."""
        try:
            # Get current grades
            grades = await self.get_player_grades(user_id)

            # Update grade - convert float to Decimal for DynamoDB compatibility
            if subject not in grades:
                grades[subject] = {}
            grades[subject][datetime.now().strftime('%Y-%m')] = Decimal(str(grade))

            # Store updated grades
            self.GRADES_TABLE.put_item(Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'GRADES',
                'grades': grades,
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error updating grade for player {user_id}: {str(e)}")
            return False

    async def get_monthly_average_grades(self, user_id: str) -> Dict[str, float]:
        """Get monthly average grades for a player."""
        try:
            grades = await self.get_player_grades(user_id)
            averages = {}

            for subject, monthly_grades in grades.items():
                if monthly_grades:
                    total = sum(monthly_grades.values())
                    count = len(monthly_grades)
                    averages[subject] = total / count

            return averages
        except Exception as e:
            logger.error(f"Error calculating monthly averages for player {user_id}: {str(e)}")
            return {}

    # --- Vote operations ---
    async def add_vote(self, vote_id: str, voter_id: str, candidate_id: str) -> bool:
        """Add a vote to the database."""
        try:
            self.VOTES_TABLE.put_item(Item={
                'PK': f'VOTE#{vote_id}',
                'SK': f'VOTER#{voter_id}',
                'candidate_id': candidate_id,
                'timestamp': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding vote for vote {vote_id}: {str(e)}")
            return False

    async def get_vote_results(self, vote_id: str) -> Dict[str, int]:
        """Get results for a vote."""
        try:
            response = self.VOTES_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': f'VOTE#{vote_id}'}
            )

            results = {}
            for item in response.get('Items', []):
                candidate_id = item['candidate_id']
                results[candidate_id] = results.get(candidate_id, 0) + 1

            return results
        except Exception as e:
            logger.error(f"Error getting results for vote {vote_id}: {str(e)}")
            return {}

    # --- Reputation operations ---
    async def update_player_reputation(self, user_id: str, amount: int) -> bool:
        """Update a player's reputation."""
        try:
            self.PLAYERS_TABLE.update_item(
                Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'},
                UpdateExpression='ADD reputation :amount',
                ExpressionAttributeValues={':amount': amount}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating reputation for player {user_id}: {str(e)}")
            return False

    # --- Database initialization ---
    async def init_db(self) -> bool:
        """Initialize database connection and perform necessary migrations."""
        try:
            # Check if DynamoDB is available
            if not self.ensure_dynamo_available():
                logger.error("DynamoDB is not available")
                return False

            # Initialize migration
            migration = DataMigration()
            
            # Perform migrations in order
            migrations = [
                'cooldowns',
                'grades',
                'events',
                'system_flags'  # Add system flags migration
            ]
            
            for migration_type in migrations:
                try:
                    logger.info(f"Starting {migration_type} migration...")
                    success = await migration.migrate(migration_type)
                    if success:
                        logger.info(f"{migration_type} migration completed successfully")
                    else:
                        logger.error(f"{migration_type} migration failed")
                except Exception as e:
                    logger.error(f"Error during {migration_type} migration: {e}")
                    continue

            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

    # --- NPC operations ---
    async def get_relevant_npcs(self, club_id: str) -> List[Dict[str, Any]]:
        """Get NPCs relevant to a club."""
        try:
            response = self.PLAYERS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND club_id = :club_id',
                ExpressionAttributeValues={
                    ':pk': 'NPC#',
                    ':club_id': club_id
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting NPCs for club {club_id}: {str(e)}")
            return []

    # --- Inventory operations ---
    async def get_player_inventory(self, user_id: str) -> Dict[str, Any]:
        """Get a player's inventory."""
        try:
            response = self.INVENTORY_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': f'PLAYER#{user_id}'}
            )

            inventory = {}
            for item in response.get('Items', []):
                item_id = item['SK'].split('#')[1]
                inventory[item_id] = item['item_data']

            return inventory
        except Exception as e:
            logger.error(f"Error getting inventory for player {user_id}: {str(e)}")
            return {}

    async def add_item_to_inventory(self, user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Add an item to a player's inventory."""
        try:
            # Ensure item_data has all required fields
            item_data_with_id = {
                'id': item_id,
                'name': item_data.get('name', ''),
                'description': item_data.get('description', ''),
                'type': item_data.get('type', ''),
                'rarity': item_data.get('rarity', 'common'),
                'effects': item_data.get('effects', {}),
                'quantity': item_data.get('quantity', 1),
                'equipped': item_data.get('equipped', False),
                'attributes': item_data.get('attributes', {}),
                'acquired_at': datetime.now().isoformat(),
                'last_used': None
            }

            # Convert numeric values to Decimal for DynamoDB
            def convert_floats_to_decimal(obj):
                if isinstance(obj, float):
                    return decimal.Decimal(str(obj))
                elif isinstance(obj, dict):
                    return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_floats_to_decimal(v) for v in obj]
                return obj

            item_data_with_id = convert_floats_to_decimal(item_data_with_id)

            self.INVENTORY_TABLE.put_item(Item={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}',
                'JogadorID': f'PLAYER#{user_id}',
                'ItemID': item_id,
                'item_data': item_data_with_id,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding item to inventory for player {user_id}: {str(e)}")
            return False

    async def remove_item_from_inventory(self, user_id: str, item_id: str) -> bool:
        """Remove an item from a player's inventory."""
        try:
            self.INVENTORY_TABLE.delete_item(
                Key={
                    'PK': f'PLAYER#{user_id}',
                    'SK': f'ITEM#{item_id}'
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error removing item from inventory for player {user_id}: {str(e)}")
            return False

    # --- Ranking operations ---
    async def get_top_players(self, limit: int = 10) -> list:
        """Get top players by level."""
        try:
            response = self.PLAYERS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': 'PLAYER#'},
                Limit=limit
            )

            players = response.get('Items', [])
            return sorted(players, key=lambda x: x.get('level', 0), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error getting top players: {str(e)}")
            return []

    async def get_top_players_by_reputation(self, limit: int = 10) -> list:
        """Get top players by reputation."""
        try:
            response = self.PLAYERS_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': 'PLAYER#'},
                Limit=limit
            )

            players = response.get('Items', [])

            # Extract user_id from PK field and add it to player objects
            for player in players:
                if 'PK' in player:
                    # Extract user_id from PK (format: 'PLAYER#{user_id}')
                    pk_parts = player['PK'].split('#')
                    if len(pk_parts) > 1:
                        player['user_id'] = pk_parts[1]

                # Ensure required fields exist
                if 'name' not in player:
                    player['name'] = f"Player {player.get('user_id', 'Unknown')}"
                if 'reputation' not in player:
                    player['reputation'] = 0
                if 'level' not in player:
                    player['level'] = 1

            return sorted(players, key=lambda x: x.get('reputation', 0), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error getting top players by reputation: {str(e)}")
            return []

    # --- Club member operations ---
    async def get_club_members(self, club_id: str) -> list:
        """Get all members of a club."""
        try:
            response = self.PLAYERS_TABLE.scan(
                FilterExpression='club_id = :club_id',
                ExpressionAttributeValues={':club_id': club_id}
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting club members for club {club_id}: {str(e)}")
            return []

    async def get_quiz_questions(self) -> List[Dict[str, Any]]:
        """Get all quiz questions from database."""
        try:
            response = self.QUIZ_QUESTIONS_TABLE.scan(
                FilterExpression='begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':sk': 'QUESTION#'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting quiz questions: {str(e)}")
            return []

    async def get_items(self) -> List[Dict[str, Any]]:
        """Get all items from database."""
        try:
            # First try to get from DynamoDB
            response = self.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': 'ITENS#',
                    ':sk': 'ITENS'
                }
            )
            items = response.get('Items', [])
            
            # If no items in DynamoDB, load from JSON file
            if not items:
                try:
                    with open('data/items.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        items = data.get('items', [])
                except Exception as e:
                    logger.error(f"Error loading items from JSON: {e}")
                    return []
            
            return items
        except Exception as e:
            logger.error(f"Error getting items: {e}")
            return []

    # --- System flag operations ---
    async def get_system_flag(self, flag_name: str) -> Optional[str]:
        """Get a system flag value."""
        try:
            response = self.SYSTEM_FLAGS_TABLE.get_item(
                Key={
                    'PK': 'SYSTEM',
                    'SK': f'FLAG#{flag_name}'
                }
            )
            return response.get('Item', {}).get('value')
        except Exception as e:
            logger.error(f"Error getting system flag {flag_name}: {str(e)}")
            return None

    async def set_system_flag(self, flag_name: str, value: str, flag_type: str = 'system') -> bool:
        """Set a system flag value."""
        try:
            item = {
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}',
                'value': value,
                'flag_type': flag_type,
                'last_updated': datetime.now().isoformat()
            }
            
            # For daily events flags, add the date field
            if flag_name.startswith('daily_events_triggered_'):
                date_str = flag_name.replace('daily_events_triggered_', '')
                try:
                    # Validate date format
                    datetime.strptime(date_str, '%Y%m%d')
                    item['date'] = date_str
                    item['flag_type'] = 'daily_events'
                except ValueError:
                    logger.warning(f"Invalid date format in flag {flag_name}")
                    return False
            
            self.SYSTEM_FLAGS_TABLE.put_item(Item=item)
            return True
        except Exception as e:
            logger.error(f"Error setting system flag {flag_name}: {str(e)}")
            return False

    async def get_daily_events_flags(self) -> List[Dict[str, Any]]:
        """Get all daily events flags."""
        try:
            response = self.SYSTEM_FLAGS_TABLE.scan(
                FilterExpression='PK = :pk AND begins_with(SK, :sk) AND flag_type = :type',
                ExpressionAttributeValues={
                    ':pk': 'SYSTEM',
                    ':sk': 'FLAG#daily_events_triggered_',
                    ':type': 'daily_events'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting daily events flags: {str(e)}")
            return []

# Create a singleton instance of DBProvider
db_provider = DBProvider()

# Create wrapper functions for all methods that need to be exported
async def get_player_async(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from database (async version)."""
    return await db_provider.get_player(user_id)

def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from database (sync version)."""
    # Create an event loop if one doesn't exist
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
            # Increased timeout to 30 seconds to prevent timeout errors
            return future.result(timeout=30)
        except concurrent.futures.TimeoutError:
            logger.error(f"Timeout waiting for get_player({user_id})")
            # Try one more time with a longer timeout
            try:
                future = asyncio.run_coroutine_threadsafe(db_provider.get_player(user_id), loop)
                return future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                logger.error(f"Second timeout waiting for get_player({user_id})")
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

async def get_top_players_by_reputation_async(limit: int = 10) -> list:
    """Get top players by reputation (async version)."""
    return await db_provider.get_top_players_by_reputation(limit)

def get_top_players_by_reputation(limit: int = 10) -> list:
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
            logger.error(f"Timeout waiting for get_top_players_by_reputation({limit})")
            return []
    else:
        return loop.run_until_complete(db_provider.get_top_players_by_reputation(limit))

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
    'clear_expired_cooldowns',
    'init_db',
    'get_player_async',
    'update_player_async',
    'get_club_async',
    'store_cooldown_async',
    'get_player_inventory_async',
    'add_item_to_inventory_async',
    'get_cooldowns_async',
    'clear_expired_cooldowns_async',
    'init_db_async',
    'get_top_players',
    'get_top_players_by_reputation',
    'get_top_players_async',
    'get_top_players_by_reputation_async',
    'store_event',
    'store_event_async'
]
