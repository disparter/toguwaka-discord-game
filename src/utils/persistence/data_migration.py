"""
Data migration module for Academia Tokugawa.

This module handles the migration of data between tables following SOLID principles.
Each migration is handled by a specific class to maintain Single Responsibility.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from utils.logging_config import get_logger
from utils.persistence.dynamodb import get_table
from decimal import Decimal

logger = get_logger('tokugawa_bot.migration')

class MigrationStrategy(ABC):
    """Abstract base class for migration strategies."""
    
    def __init__(self, db_provider):
        self.db_provider = db_provider
    
    @abstractmethod
    async def migrate(self) -> bool:
        """Execute the migration strategy."""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Validate the migration results."""
        pass

class ItemsMigration(MigrationStrategy):
    """Handles migration of items from JSON files to items table."""
    
    def _convert_to_decimal(self, value):
        """Convert numeric values to Decimal for DynamoDB compatibility."""
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, dict):
            return {k: self._convert_to_decimal(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._convert_to_decimal(v) for v in value]
        return value
    
    async def migrate(self) -> bool:
        try:
            # Migrate items from all JSON files in the items directory
            items_dir = os.path.join('data', 'economy', 'items')
            if os.path.exists(items_dir):
                items_table = self.db_provider.ITEMS_TABLE
                migrated_items = 0
                
                # Process each JSON file in the items directory
                for filename in os.listdir(items_dir):
                    if not filename.endswith('.json'):
                        continue
                        
                    file_path = os.path.join(items_dir, filename)
                    logger.info(f"Processing items file: {filename}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        items_data = json.load(f)
                    
                    # Process each item in the file (items_data is a list)
                    for item_data in items_data:
                        try:
                            item_id = item_data.get('id')
                            if not item_id:
                                logger.warning(f"Item without ID found in {filename}, skipping...")
                                continue
                                
                            # Convert numeric values to Decimal
                            effects = self._convert_to_decimal(item_data.get('effects', {}))
                            price = self._convert_to_decimal(item_data.get('price', 0))
                                
                            # Create the item to be inserted
                            item = {
                                'PK': f'ITEM#{item_id}',
                                'SK': 'METADATA',
                                'name': item_data.get('name', ''),
                                'description': item_data.get('description', ''),
                                'type': item_data.get('type', ''),
                                'category': item_data.get('category', ''),
                                'rarity': item_data.get('rarity', ''),
                                'effects': effects,
                                'price': price,
                                'is_available': True,
                                'created_at': datetime.now().isoformat(),
                                'last_updated': datetime.now().isoformat()
                            }
                            
                            logger.info(f"Inserting item: {item}")
                            
                            # Use put_item with the item dictionary
                            items_table.put_item(Item=item)
                            migrated_items += 1
                            
                        except Exception as e:
                            logger.error(f"Error migrating item {item_id}: {e}")
                            continue
                
                logger.info(f"Successfully migrated {migrated_items} items")
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrating items: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            return False

    async def validate(self) -> bool:
        try:
            # Validate items migration
            items_table = self.db_provider.ITEMS_TABLE
            items_response = items_table.scan(
                FilterExpression='begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':sk': 'METADATA'
                }
            )
            items = items_response.get('Items', [])
            
            logger.info(f"Found {len(items)} items in the new table")
            
            # Validate each item entry
            for item in items:
                if not all(k in item for k in ['PK', 'SK', 'name', 'type', 'category', 'rarity']):
                    logger.warning(f"Invalid item entry found: {item}")
                    return False
                
                # Validate that effects is a dictionary
                if not isinstance(item.get('effects', {}), dict):
                    logger.warning(f"Invalid effects format in item {item['PK']}")
                    return False
                
                # Validate that price is a Decimal
                if not isinstance(item.get('price', Decimal('0')), Decimal):
                    logger.warning(f"Invalid price format in item {item['PK']}")
                    return False
            
            logger.info("Items migration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating items migration: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            return False


class DataMigration:
    """Main class for handling data migrations."""
    
    def __init__(self, db_provider):
        self.db_provider = db_provider
        self.migrations = {
            'items': ItemsMigration(db_provider)

        }
    
    async def migrate_data(self) -> bool:
        """Run all migrations in sequence."""
        try:
            # Run migrations in order
            migrations = [
                'items'
            ]
            
            for migration_name in migrations:
                logger.info(f"Starting {migration_name} migration...")
                success = await self.run_migration(migration_name)
                if not success:
                    logger.error(f"{migration_name} migration failed")
                    return False
                logger.info(f"{migration_name} migration completed successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error during data migration: {e}")
            return False
    
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