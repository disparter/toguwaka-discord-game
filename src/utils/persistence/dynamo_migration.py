"""
Script to normalize player data in DynamoDB.
This script will:
1. Move inventory data from players table to inventory table
2. Add missing default attributes to players
3. Remove inventory information from player data
"""

import os
import boto3
import json
import logging
import time
from typing import Dict, List, Any
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('tokugawa_bot')

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

# Get table names from environment variables
PLAYERS_TABLE = os.getenv('DYNAMODB_PLAYERS_TABLE', 'tokugawa-players')
INVENTORY_TABLE = os.getenv('DYNAMODB_INVENTORY_TABLE', 'tokugawa-inventory')

# Default values for player attributes
DEFAULT_PLAYER_VALUES = {
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
    'strength_level': 1
}

def wait_for_dynamodb():
    """Wait for DynamoDB tables to be ready."""
    logger.info("Waiting for DynamoDB tables to be ready...")
    max_retries = 30
    retry_delay = 2

    for i in range(max_retries):
        try:
            # Check if tables exist and are active
            players_table = dynamodb_client.describe_table(TableName=PLAYERS_TABLE)
            inventory_table = dynamodb_client.describe_table(TableName=INVENTORY_TABLE)

            if (players_table['Table']['TableStatus'] == 'ACTIVE' and 
                inventory_table['Table']['TableStatus'] == 'ACTIVE'):
                logger.info("DynamoDB tables are ready!")
                return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"Tables not found yet. Retry {i+1}/{max_retries}")
            else:
                logger.error(f"Error checking tables: {str(e)}")
                return False

        time.sleep(retry_delay)

    logger.error("Timeout waiting for DynamoDB tables")
    return False

def migrate_inventory(inventory_str: str, user_id: str) -> List[Dict[str, Any]]:
    """Migrate inventory data to new format."""
    try:
        inventory = json.loads(inventory_str)
        items = []
        for item_id, item_data in inventory.items():
            items.append({
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}',
                'item_data': item_data,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
        return items
    except Exception as e:
        logger.error(f"Error parsing inventory for player {user_id}: {str(e)}")
        return []

async def normalize_player_data() -> bool:
    """Normalize all players' data in DynamoDB.

    Returns:
        bool: True if normalization was successful, False otherwise
    """
    logger.info("Starting player data normalization process...")

    # Wait for DynamoDB to be ready
    if not wait_for_dynamodb():
        logger.error("Failed to start normalization: DynamoDB not ready")
        return False

    # Add more detailed logging
    logger.info("DynamoDB is ready, proceeding with normalization")

    try:
        # Get table references
        logger.info(f"Getting table references for {PLAYERS_TABLE} and {INVENTORY_TABLE}...")
        players_table = dynamodb.Table(PLAYERS_TABLE)
        inventory_table = dynamodb.Table(INVENTORY_TABLE)
        logger.info("Table references obtained successfully")

        logger.info("Scanning players table...")
        try:
            # Scan all players
            response = players_table.scan()
            players = response.get('Items', [])
            logger.info(f"Initial scan returned {len(players)} players")

            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                logger.info(f"Pagination detected, fetching more players...")
                response = players_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                new_players = response.get('Items', [])
                logger.info(f"Additional scan returned {len(new_players)} more players")
                players.extend(new_players)
        except Exception as e:
            logger.error(f"Error scanning players table: {str(e)}")
            return False

        logger.info(f"Found {len(players)} players to normalize")

        # Process each player
        success_count = 0
        error_count = 0
        logger.info("Starting to process players one by one...")

        for index, player in enumerate(players):
            player_id = player.get('PK', 'unknown')
            logger.info(f"Processing player {index+1}/{len(players)}: {player_id}")

            try:
                # Extract and migrate inventory if it exists
                inventory_str = player.pop('inventory', None)
                if inventory_str:
                    logger.info(f"Found inventory data for player {player_id}, migrating...")
                    inventory_items = migrate_inventory(inventory_str, player['PK'].split('#')[1])
                    logger.info(f"Migrating {len(inventory_items)} items for player {player_id}")
                    for item_index, item in enumerate(inventory_items):
                        inventory_table.put_item(Item=item)
                        if item_index % 10 == 0 and item_index > 0:  # Log every 10 items
                            logger.info(f"Migrated {item_index}/{len(inventory_items)} items for player {player_id}")
                    logger.info(f"Successfully migrated all inventory items for player {player_id}")
                else:
                    logger.info(f"No inventory data found for player {player_id}")

                # Add missing default attributes
                missing_attrs = []
                for key, value in DEFAULT_PLAYER_VALUES.items():
                    if key not in player or player[key] is None:
                        player[key] = value
                        missing_attrs.append(key)

                if missing_attrs:
                    logger.info(f"Added missing attributes for player {player_id}: {', '.join(missing_attrs)}")
                else:
                    logger.info(f"No missing attributes for player {player_id}")

                # Update timestamps
                player['last_active'] = datetime.now().isoformat()
                if 'created_at' not in player:
                    player['created_at'] = datetime.now().isoformat()
                    logger.info(f"Added missing created_at timestamp for player {player_id}")

                # Write updated player data
                logger.info(f"Writing updated data for player {player_id} to DynamoDB...")
                players_table.put_item(Item=player)
                logger.info(f"Successfully normalized player data for {player_id}")
                success_count += 1

            except Exception as e:
                logger.error(f"Error processing player {player_id}: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                error_count += 1
                continue

            # Log progress every 10 players
            if (index + 1) % 10 == 0:
                logger.info(f"Progress: {index+1}/{len(players)} players processed ({success_count} successful, {error_count} errors)")

        logger.info(f"Normalization completed:")
        logger.info(f"- Total players processed: {len(players)}")
        logger.info(f"- Successfully normalized: {success_count}")
        logger.info(f"- Errors encountered: {error_count}")
        return success_count == len(players)

    except Exception as e:
        logger.error(f"Error during normalization: {str(e)}")
        return False

# Export the normalize_player_data function
__all__ = ['normalize_player_data'] 
