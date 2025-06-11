"""
Data migration module for Academia Tokugawa.

This module handles the migration of data between tables following SOLID principles.
Each migration is handled by a specific class to maintain Single Responsibility.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from utils.persistence.db_provider import db_provider

logger = logging.getLogger('tokugawa_bot')

class MigrationStrategy(ABC):
    """Abstract base class for migration strategies."""
    
    @abstractmethod
    async def migrate(self) -> bool:
        """Execute the migration strategy."""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Validate the migration results."""
        pass

class GradesMigration(MigrationStrategy):
    """Handles migration of grades from players table to grades table."""
    
    async def migrate(self) -> bool:
        try:
            # Get all players from players table
            response = await db_provider.PLAYERS_TABLE.scan()
            players = response.get('Items', [])
            
            # Migrate each player's grades
            for player in players:
                player_id = player.get('PK').replace('PLAYER#', '')
                grades = player.get('grades', {})
                
                if grades:
                    for subject, grade_data in grades.items():
                        await db_provider.GRADES_TABLE.put_item(
                            Item={
                                'PK': f'PLAYER#{player_id}',
                                'SK': f'SUBJECT#{subject}',
                                'grade': grade_data.get('grade', 0),
                                'last_updated': grade_data.get('last_updated', datetime.now().isoformat()),
                                'subject': subject,
                                'semester': grade_data.get('semester', 1)
                            }
                        )
            
            return True
        except Exception as e:
            logger.error(f"Error migrating grades: {e}")
            return False

    async def validate(self) -> bool:
        try:
            # Check if grades were migrated correctly
            response = await db_provider.GRADES_TABLE.scan(
                FilterExpression='begins_with(SK, :sk)',
                ExpressionAttributeValues={':sk': 'SUBJECT#'}
            )
            return len(response.get('Items', [])) > 0
        except Exception as e:
            logger.error(f"Error validating grades migration: {e}")
            return False

class CooldownsMigration(MigrationStrategy):
    """Handles migration of cooldowns from main table to cooldowns table."""
    
    async def migrate(self) -> bool:
        try:
            # Get all cooldowns from main table
            response = await db_provider.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': 'COOLDOWN#'}
            )
            
            cooldowns = response.get('Items', [])
            
            # Migrate each cooldown to the cooldowns table
            for cooldown in cooldowns:
                user_id = cooldown.get('PK').replace('COOLDOWN#', '')
                command = cooldown.get('SK').replace('COMMAND#', '')
                
                await db_provider.COOLDOWNS_TABLE.put_item(
                    Item={
                        'PK': f'PLAYER#{user_id}',
                        'SK': f'COMMAND#{command}',
                        'expiry_time': cooldown.get('expiry_time'),
                        'command': command,
                        'created_at': cooldown.get('created_at', datetime.now().isoformat())
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error migrating cooldowns: {e}")
            return False

    async def validate(self) -> bool:
        try:
            # Check if cooldowns were migrated correctly
            response = await db_provider.COOLDOWNS_TABLE.scan()
            return len(response.get('Items', [])) > 0
        except Exception as e:
            logger.error(f"Error validating cooldowns migration: {e}")
            return False

class EventsMigration(MigrationStrategy):
    """Handles migration of events from AcademiaTokugawa to events table."""
    
    async def migrate(self) -> bool:
        try:
            # Get all events from AcademiaTokugawa
            response = await db_provider.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': 'ACADEMIA#'}
            )
            
            events = response.get('Items', [])
            
            # Migrate each event
            for event in events:
                event_id = event.get('PK').replace('ACADEMIA#', '')
                event_type = event.get('type', 'random')
                
                await db_provider.EVENTS_TABLE.put_item(
                    Item={
                        'PK': f'EVENT#{event_id}',
                        'SK': f'TYPE#{event_type}',
                        'name': event.get('name', ''),
                        'description': event.get('description', ''),
                        'type': event_type,
                        'data': event.get('data', {}),
                        'created_at': event.get('created_at', datetime.now().isoformat()),
                        'expires_at': event.get('expires_at'),
                        'participants': event.get('participants', []),
                        'is_active': event.get('is_active', True)
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error migrating events: {e}")
            return False

    async def validate(self) -> bool:
        try:
            # Check if events were migrated correctly
            response = await db_provider.EVENTS_TABLE.scan(
                FilterExpression='begins_with(SK, :sk)',
                ExpressionAttributeValues={':sk': 'TYPE#'}
            )
            return len(response.get('Items', [])) > 0
        except Exception as e:
            logger.error(f"Error validating events migration: {e}")
            return False

class StoryProgressMigration(MigrationStrategy):
    """Handles migration of story progress from main table to story table."""
    
    async def migrate(self) -> bool:
        try:
            # Get all players from main table
            response = await db_provider.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': 'PLAYER#'}
            )
            
            players = response.get('Items', [])
            
            # Migrate each player's story progress
            for player in players:
                player_id = player.get('PK').replace('PLAYER#', '')
                story_progress = player.get('story_progress', {})
                
                if story_progress:
                    await db_provider.STORY_TABLE.put_item(
                        Item={
                            'PK': f'PLAYER#{player_id}',
                            'SK': 'STORY_PROGRESS',
                            'current_chapter': story_progress.get('current_chapter', 1),
                            'completed_chapters': story_progress.get('completed_chapters', []),
                            'choices': story_progress.get('choices', {}),
                            'last_updated': datetime.now().isoformat()
                        }
                    )
            
            return True
        except Exception as e:
            logger.error(f"Error migrating story progress: {e}")
            return False

    async def validate(self) -> bool:
        try:
            # Check if story progress was migrated correctly
            response = await db_provider.STORY_TABLE.scan(
                FilterExpression='SK = :sk',
                ExpressionAttributeValues={':sk': 'STORY_PROGRESS'}
            )
            return len(response.get('Items', [])) > 0
        except Exception as e:
            logger.error(f"Error validating story progress migration: {e}")
            return False

class InventoryMigration(MigrationStrategy):
    """Handles migration of inventory data from main table to inventory table."""
    
    async def migrate(self) -> bool:
        try:
            # Get all players from main table
            response = await db_provider.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': 'PLAYER#'}
            )
            
            players = response.get('Items', [])
            
            # Migrate each player's inventory
            for player in players:
                player_id = player.get('PK').replace('PLAYER#', '')
                inventory = player.get('inventory', {})
                
                if inventory:
                    # Migrate each item in the inventory
                    for item_id, item_data in inventory.items():
                        await db_provider.INVENTORY_TABLE.put_item(
                            Item={
                                'PK': f'PLAYER#{player_id}',
                                'SK': f'ITEM#{item_id}',
                                'quantity': item_data.get('quantity', 1),
                                'equipped': item_data.get('equipped', False),
                                'attributes': item_data.get('attributes', {}),
                                'acquired_at': item_data.get('acquired_at', datetime.now().isoformat()),
                                'last_used': item_data.get('last_used')
                            }
                        )
            
            return True
        except Exception as e:
            logger.error(f"Error migrating inventory: {e}")
            return False

    async def validate(self) -> bool:
        try:
            # Check if inventory items were migrated correctly
            response = await db_provider.INVENTORY_TABLE.scan(
                FilterExpression='begins_with(SK, :sk)',
                ExpressionAttributeValues={':sk': 'ITEM#'}
            )
            return len(response.get('Items', [])) > 0
        except Exception as e:
            logger.error(f"Error validating inventory migration: {e}")
            return False

class ItemsAndQuizMigration(MigrationStrategy):
    """Handles migration of items and quiz questions from JSON files to their respective tables."""
    
    async def migrate(self) -> bool:
        try:
            # Load items from JSON
            with open('data/economy/items.json', 'r') as f:
                items = json.load(f)
            
            # Migrate items
            for item_id, item_data in items.items():
                await db_provider.ITEMS_TABLE.put_item(
                    Item={
                        'PK': f'ITEM#{item_id}',
                        'SK': 'ITEM',
                        'name': item_data.get('name', ''),
                        'description': item_data.get('description', ''),
                        'type': item_data.get('type', ''),
                        'rarity': item_data.get('rarity', 'common'),
                        'effects': item_data.get('effects', {}),
                        'price': item_data.get('price', 0),
                        'is_available': item_data.get('is_available', True)
                    }
                )
            
            # Load quiz questions from JSON
            with open('data/economy/quiz_questions.json', 'r') as f:
                quiz_questions = json.load(f)
            
            # Migrate quiz questions
            for question_id, question_data in quiz_questions.items():
                await db_provider.QUIZ_TABLE.put_item(
                    Item={
                        'PK': f'QUESTION#{question_id}',
                        'SK': 'QUIZ',
                        'question': question_data.get('question', ''),
                        'options': question_data.get('options', []),
                        'correct_answer': question_data.get('correct_answer', ''),
                        'difficulty': question_data.get('difficulty', 'medium'),
                        'category': question_data.get('category', 'general'),
                        'points': question_data.get('points', 10)
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error migrating items and quiz questions: {e}")
            return False

    async def validate(self) -> bool:
        try:
            # Check if items were migrated
            items_response = await db_provider.ITEMS_TABLE.scan(
                FilterExpression='SK = :sk',
                ExpressionAttributeValues={':sk': 'ITEM'}
            )
            
            # Check if quiz questions were migrated
            quiz_response = await db_provider.QUIZ_TABLE.scan(
                FilterExpression='SK = :sk',
                ExpressionAttributeValues={':sk': 'QUIZ'}
            )
            
            return len(items_response.get('Items', [])) > 0 and len(quiz_response.get('Items', [])) > 0
        except Exception as e:
            logger.error(f"Error validating items and quiz migration: {e}")
            return False

class DataMigration:
    """Main class for handling data migrations."""
    
    def __init__(self):
        self.migrations = {
            'grades': GradesMigration(),
            'cooldowns': CooldownsMigration(),
            'events': EventsMigration(),
            'story': StoryProgressMigration(),
            'inventory': InventoryMigration(),
            'items_and_quiz': ItemsAndQuizMigration()
        }
    
    async def run_migration(self, migration_name: str) -> bool:
        """Run a specific migration."""
        if migration_name not in self.migrations:
            logger.error(f"Migration {migration_name} not found")
            return False
            
        migration = self.migrations[migration_name]
        
        # Run migration
        success = await migration.migrate()
        if not success:
            logger.error(f"Migration {migration_name} failed")
            return False
            
        # Validate migration
        valid = await migration.validate()
        if not valid:
            logger.error(f"Migration {migration_name} validation failed")
            return False
            
        logger.info(f"Migration {migration_name} completed successfully")
        return True

# Create singleton instance
data_migration = DataMigration() 