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
logger = logging.getLogger(__name__)

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

    try:
        # Get table references
        players_table = dynamodb.Table(PLAYERS_TABLE)
        inventory_table = dynamodb.Table(INVENTORY_TABLE)

        logger.info("Scanning players table...")
        # Scan all players
        response = players_table.scan()
        players = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = players_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            players.extend(response.get('Items', []))

        logger.info(f"Found {len(players)} players to normalize")

        # Process each player
        success_count = 0
        error_count = 0
        for player in players:
            try:
                # Extract and migrate inventory if it exists
                inventory_str = player.pop('inventory', None)
                if inventory_str:
                    inventory_items = migrate_inventory(inventory_str, player['PK'].split('#')[1])
                    for item in inventory_items:
                        inventory_table.put_item(Item=item)
                    logger.info(f"Migrated inventory for player {player['PK']}")

                # Add missing default attributes
                for key, value in DEFAULT_PLAYER_VALUES.items():
                    if key not in player or player[key] is None:
                        player[key] = value

                # Update timestamps
                player['last_active'] = datetime.now().isoformat()
                if 'created_at' not in player:
                    player['created_at'] = datetime.now().isoformat()

                # Write updated player data
                players_table.put_item(Item=player)
                logger.info(f"Normalized player data for {player['PK']}")
                success_count += 1

            except Exception as e:
                logger.error(f"Error processing player {player.get('PK', 'unknown')}: {str(e)}")
                error_count += 1
                continue

        logger.info(f"Normalization completed:")
        logger.info(f"- Total players processed: {len(players)}")
        logger.info(f"- Successfully normalized: {success_count}")
        logger.info(f"- Errors encountered: {error_count}")
        return success_count == len(players)

    except Exception as e:
        logger.error(f"Error during normalization: {str(e)}")
        return False 