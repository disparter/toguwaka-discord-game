"""
DynamoDB implementation for player data persistence.
"""

import boto3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.logging_config import get_logger
from utils.persistence.dynamodb import (
    get_table,
    put_item,
    get_item,
    query_items,
    scan_items,
    update_item,
    delete_item,
    TABLES,
    handle_dynamo_error,
    DynamoDBOperationError
)
from botocore.exceptions import ClientError

logger = get_logger('tokugawa_bot.players')

class DynamoDBPlayers:
    """DynamoDB implementation for player data persistence."""
    
    def __init__(self):
        """Initialize DynamoDB connection."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table = None
    
    def init_table(self):
        """Initialize the table reference."""
        if self.table is None:
            from utils.persistence.db_provider import db_provider
            self.table = db_provider.PLAYERS_TABLE
    
    async def get_player(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get player data from DynamoDB."""
        try:
            if not user_id:
                logger.warning("Empty user_id provided to get_player")
                return None
            
            # Ensure user_id is a string
            user_id = str(user_id)
            
            # Initialize table if needed
            self.init_table()
            
            # Get player data
            response = self.table.get_item(
                Key={
                    'PK': f'PLAYER#{user_id}',
                    'SK': 'PROFILE'
                }
            )
            
            if 'Item' not in response:
                logger.info(f"No player found for user_id: {user_id}")
                return None
            
            item = response['Item']
            
            # Handle inventory serialization
            if isinstance(item.get('inventory'), str):
                try:
                    item['inventory'] = json.loads(item['inventory'])
                except Exception as e:
                    logger.warning(f"Could not decode inventory for player {user_id}: {e}")
                    item['inventory'] = {}
            
            # Ensure inventory is a dictionary
            if not isinstance(item.get('inventory'), dict):
                item['inventory'] = {}
            
            # Normalize inventory items
            for item_id, item_data in item['inventory'].items():
                if isinstance(item_data, str):
                    try:
                        item['inventory'][item_id] = json.loads(item_data)
                    except:
                        item['inventory'][item_id] = {
                            'id': item_id,
                            'quantity': 1
                        }
                elif not isinstance(item_data, dict):
                    item['inventory'][item_id] = {
                        'id': item_id,
                        'quantity': 1
                    }
            
            # Check for missing attributes
            missing_attrs = []
            required_attrs = ['power_stat', 'dexterity', 'intellect', 'charisma', 'exp', 'hp', 'tusd', 'level', 'reputation']
            for attr in required_attrs:
                if attr not in item:
                    missing_attrs.append(attr)
                    item[attr] = 0  # Set default value
            
            # If any attributes were missing, update the player record
            if missing_attrs:
                logger.info(f"Updating player {user_id} with missing attributes: {missing_attrs}")
                update_item = {
                    'PK': f"PLAYER#{user_id}",
                    'SK': 'PROFILE',
                    **item
                }
                # Convert numeric values to Decimal for DynamoDB
                for k, v in update_item.items():
                    if isinstance(v, (int, float)):
                        update_item[k] = decimal.Decimal(str(v))
                    elif k == 'inventory' and isinstance(v, dict):
                        update_item[k] = json.dumps(v)
                try:
                    await self.table.put_item(Item=update_item)
                    logger.info(f"Successfully updated player {user_id} with missing attributes")
                except Exception as e:
                    logger.error(f"Failed to update player {user_id} with missing attributes: {e}")
                    # Continue with the current item data even if update fails
            
            logger.debug(f"Retrieved player data for {user_id}")
            return item
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ProvisionedThroughputExceededException':
                logger.warning(f"Provisioned throughput exceeded for player {user_id}")
                # Return None to allow retry at a higher level
                return None
            elif error_code == 'ThrottlingException':
                logger.warning(f"Request throttled for player {user_id}")
                # Return None to allow retry at a higher level
                return None
            else:
                logger.error(f"DynamoDB error getting player {user_id}: {e}")
                raise DynamoDBOperationError(f"Failed to get player: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting player {user_id}: {e}")
            raise DynamoDBOperationError(f"Failed to get player: {e}") from e
    
    async def create_player(self, user_id: str, name: str, **kwargs) -> bool:
        """Create a new player in DynamoDB."""
        if not user_id or not name:
            return False
        try:
            item = {
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE',
                'name': name,
                'created_at': datetime.now().isoformat(),
                'level': 1,
                'exp': 0,
                'coins': 100,
                'reputation': 0,
                'club_id': None,
                'story_progress': {},
                **kwargs
            }
            
            await self.table.put_item(Item=item)
            return True
        except Exception as e:
            logger.error(f"Error creating player: {e}")
            return False
    
    async def update_player(self, user_id: str, **kwargs) -> bool:
        """Update player data in DynamoDB."""
        if not user_id:
            return False
        try:
            # Ensure user_id is a string
            user_id = str(user_id)
            
            # Initialize table if needed
            self.init_table()
            
            # Get current player data
            current_data = await self.get_player(user_id)
            if not current_data:
                return False
            
            # Update fields
            for key, value in kwargs.items():
                current_data[key] = value
            
            # Update timestamp
            current_data['updated_at'] = datetime.now().isoformat()
            
            # Update in DynamoDB
            await self.table.put_item(Item=current_data)
            return True
        except Exception as e:
            logger.error(f"Error updating player: {e}")
            return False
    
    async def get_all_players(self) -> list:
        """Get all players from DynamoDB."""
        try:
            # Initialize table if needed
            self.init_table()
            
            response = self.table.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={
                    ':pk': 'PLAYER#'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting all players: {e}")
            return []
    
    async def get_top_players(self, limit: int = 10) -> list:
        """Get top players by level."""
        try:
            # Initialize table if needed
            self.init_table()
            
            response = self.table.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={
                    ':pk': 'PLAYER#'
                }
            )
            
            players = response.get('Items', [])
            players.sort(key=lambda x: (x.get('level', 0), x.get('exp', 0)), reverse=True)
            return players[:limit]
        except Exception as e:
            logger.error(f"Error getting top players: {e}")
            return []

# Create singleton instance
_players = None

def get_players():
    """Get or create the singleton instance."""
    global _players
    if _players is None:
        _players = DynamoDBPlayers()
    return _players

# Export functions
def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    return get_players().get_player(user_id)

def create_player(user_id: str, name: str, **kwargs) -> bool:
    return get_players().create_player(user_id, name, **kwargs)

def update_player(user_id: str, **kwargs) -> bool:
    return get_players().update_player(user_id, **kwargs)

def get_all_players() -> list:
    return get_players().get_all_players()

def get_top_players(limit: int = 10) -> list:
    return get_players().get_top_players(limit)

@handle_dynamo_error
async def get_club_members(club_id: str) -> List[Dict[str, Any]]:
    """Get all players in a club."""
    try:
        table = get_table(TABLES['players'])
        response = await table.scan(
            FilterExpression='club_id = :club_id',
            ExpressionAttributeValues={
                ':club_id': club_id
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting club members: {e}")
        return []

@handle_dynamo_error
async def update_player_stats(user_id: str, stats: Dict[str, int]) -> bool:
    """Update a player's stats."""
    try:
        # Convert stats to Decimal
        decimal_stats = {
            k: decimal.Decimal(str(v)) for k, v in stats.items()
        }
        return await update_player(user_id, **decimal_stats)
    except Exception as e:
        logger.error(f"Error updating player stats: {e}")
        return False

@handle_dynamo_error
async def update_player_inventory(user_id: str, inventory: Dict[str, Any]) -> bool:
    """Update a player's inventory."""
    try:
        return await update_player(user_id, inventory=json.dumps(inventory))
    except Exception as e:
        logger.error(f"Error updating player inventory: {e}")
        return False

@handle_dynamo_error
async def delete_player(user_id: str) -> bool:
    """Delete a player from DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        await table.delete_item(
            Key={
                'PK': f"PLAYER#{user_id}",
                'SK': 'PROFILE'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting player: {e}")
        return False 