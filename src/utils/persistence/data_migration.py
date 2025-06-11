"""
Data migration module for Academia Tokugawa.

This module handles the one-time migration of static data from JSON files
to DynamoDB tables with the new PK/SK pattern.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.persistence.db_provider import db_provider

logger = logging.getLogger('tokugawa_bot')

class DataMigration:
    """Handles one-time migration of static data to DynamoDB."""

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'data')
        self.table_prefixes = {
            'eventos': 'EVENTOS#',
            'cooldowns': 'COOLDOWN#',
            'itens': 'ITENS#',
            'quiz_questions': 'QUIZQUESTION#',
            'quiz_answers': 'QUIZANSWER#'
        }

    async def check_table_empty(self, prefix: str) -> bool:
        """Check if a table is empty by scanning for items with the given prefix."""
        try:
            response = db_provider.MAIN_TABLE.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={':pk': prefix},
                Limit=1
            )
            return not response.get('Items')
        except Exception as e:
            logger.error(f"Error checking if table {prefix} is empty: {e}")
            return False

    def load_json_data(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Load data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON data from {file_path}: {e}")
            return None

    async def migrate_table(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Migrate data from JSON to DynamoDB table."""
        prefix = self.table_prefixes.get(table_name)
        if not prefix:
            logger.error(f"Unknown table name: {table_name}")
            return False

        try:
            # Check if table is empty
            if not await self.check_table_empty(prefix):
                logger.info(f"Table {table_name} already has data, skipping migration")
                return True

            # Prepare items for batch write
            items = []
            for item in data:
                item_id = str(item.get('id', len(items) + 1))
                dynamo_item = {
                    'PK': f"{prefix}{item_id}",
                    'SK': prefix.rstrip('#'),
                    **item
                }
                items.append(dynamo_item)

            # Write items in batches of 25 (DynamoDB batch write limit)
            batch_size = 25
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                with db_provider.MAIN_TABLE.batch_writer() as batch_writer:
                    for item in batch:
                        batch_writer.put_item(Item=item)

            logger.info(f"Successfully migrated {len(items)} items to table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error migrating table {table_name}: {e}")
            return False

    async def migrate_all_data(self) -> bool:
        """Migrate all static data to DynamoDB tables."""
        try:
            # Migrate eventos
            eventos_path = os.path.join(self.data_dir, 'events', 'random_events.json')
            eventos_data = self.load_json_data(eventos_path)
            if eventos_data:
                await self.migrate_table('eventos', eventos_data)

            # Migrate itens
            itens_path = os.path.join(self.data_dir, 'economy', 'items.json')
            itens_data = self.load_json_data(itens_path)
            if itens_data:
                await self.migrate_table('itens', itens_data)

            # Migrate quiz questions
            quiz_path = os.path.join(self.data_dir, 'story_mode', 'quiz_questions.json')
            quiz_data = self.load_json_data(quiz_path)
            if quiz_data:
                await self.migrate_table('quiz_questions', quiz_data)

            # Migrate quiz answers
            answers_path = os.path.join(self.data_dir, 'story_mode', 'quiz_answers.json')
            answers_data = self.load_json_data(answers_path)
            if answers_data:
                await self.migrate_table('quiz_answers', answers_data)

            return True
        except Exception as e:
            logger.error(f"Error migrating data: {e}")
            return False

    async def migrate_data(self) -> bool:
        """Migrate all static data from JSON files to DynamoDB."""
        try:
            # Migrate static data to AcademiaTokugawa table
            await self.migrate_quiz_questions()
            await self.migrate_items()

            # Migrate dynamic data to main table
            await self.migrate_events()
            await self.migrate_cooldowns()

            return True
        except Exception as e:
            logger.error(f"Error migrating data: {str(e)}")
            return False

    async def migrate_quiz_questions(self) -> bool:
        """Migrate quiz questions to AcademiaTokugawa table."""
        try:
            if not await self.check_table_empty('QUIZQUESTION#'):
                logger.info("Quiz questions table is not empty, skipping migration")
                return True

            questions = self.load_json_data(os.path.join(self.data_dir, 'story_mode', 'quiz_questions.json'))
            if not questions:
                logger.error("No quiz questions data found")
                return False

            for question in questions:
                question_id = question.get('id')
                if not question_id:
                    continue

                # Store question
                await db_provider.ACADEMIA_TABLE.put_item(
                    Item={
                        'PK': f'QUIZQUESTION#{question_id}',
                        'SK': 'QUIZQUESTION',
                        **question
                    }
                )

                # Store answers
                answers = question.get('answers', [])
                for answer in answers:
                    answer_id = answer.get('id')
                    if not answer_id:
                        continue

                    await db_provider.ACADEMIA_TABLE.put_item(
                        Item={
                            'PK': f'QUIZANSWER#{answer_id}',
                            'SK': f'QUESTION#{question_id}',
                            **answer
                        }
                    )

            logger.info("Successfully migrated quiz questions")
            return True
        except Exception as e:
            logger.error(f"Error migrating quiz questions: {str(e)}")
            return False

    async def migrate_items(self) -> bool:
        """Migrate items to AcademiaTokugawa table."""
        try:
            if not await self.check_table_empty('ITENS#'):
                logger.info("Items table is not empty, skipping migration")
                return True

            items = self.load_json_data(os.path.join(self.data_dir, 'economy', 'items.json'))
            if not items:
                logger.error("No items data found")
                return False

            for item in items:
                item_id = item.get('id')
                if not item_id:
                    continue

                await db_provider.ACADEMIA_TABLE.put_item(
                    Item={
                        'PK': f'ITENS#{item_id}',
                        'SK': 'ITENS',
                        **item
                    }
                )

            logger.info("Successfully migrated items")
            return True
        except Exception as e:
            logger.error(f"Error migrating items: {str(e)}")
            return False

    async def migrate_events(self) -> bool:
        """Migrate events to main table."""
        try:
            if not await self.check_table_empty('EVENTOS#'):
                logger.info("Events table is not empty, skipping migration")
                return True

            events = self.load_json_data(os.path.join(self.data_dir, 'events', 'random_events.json'))
            if not events:
                logger.error("No events data found")
                return False

            for event in events:
                event_id = event.get('id')
                if not event_id:
                    continue

                await db_provider.MAIN_TABLE.put_item(
                    Item={
                        'PK': f'EVENTOS#{event_id}',
                        'SK': 'EVENTOS',
                        **event
                    }
                )

            logger.info("Successfully migrated events")
            return True
        except Exception as e:
            logger.error(f"Error migrating events: {str(e)}")
            return False

    async def migrate_cooldowns(self) -> bool:
        """Migrate cooldowns to main table."""
        try:
            if not await self.check_table_empty('COOLDOWN#'):
                logger.info("Cooldowns table is not empty, skipping migration")
                return True

            cooldowns = self.load_json_data(os.path.join(self.data_dir, 'cooldowns.json'))
            if not cooldowns:
                logger.error("No cooldowns data found")
                return False

            for cooldown in cooldowns:
                user_id = cooldown.get('user_id')
                command = cooldown.get('command')
                if not user_id or not command:
                    continue

                await db_provider.MAIN_TABLE.put_item(
                    Item={
                        'PK': f'COOLDOWN#{user_id}',
                        'SK': f'COMMAND#{command}',
                        **cooldown
                    }
                )

            logger.info("Successfully migrated cooldowns")
            return True
        except Exception as e:
            logger.error(f"Error migrating cooldowns: {str(e)}")
            return False

# Create a singleton instance
data_migration = DataMigration() 