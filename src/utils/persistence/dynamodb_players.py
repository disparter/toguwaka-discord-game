"""
Player operations for DynamoDB.
"""

import decimal
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
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

logger = get_logger('tokugawa_bot.players')

@handle_dynamo_error
async def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        response = await table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            }
        )
        
        if 'Item' not in response:
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
                
        # If any attributes were missing, update the player record
        if missing_attrs:
            logger.info(f"Updating player {user_id} with missing attributes")
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
            await table.put_item(Item=update_item)
            logger.info(f"Successfully updated player {user_id} with missing attributes")
            
        logger.info(f"Final player data after normalization: {item}")
        return item
    except Exception as e:
        logger.error(f"Error getting player: {e}")
        raise DynamoDBOperationError(f"Failed to get player: {e}") from e

@handle_dynamo_error
async def create_player(user_id: str, name: str, **kwargs) -> bool:
    """Create a new player in DynamoDB."""
    if not user_id or not name:
        return False
    try:
        table = get_table(TABLES['players'])
        # Default values for required attributes
        defaults = {
            'power_stat': 10,
            'dexterity': 10,
            'intellect': 10,
            'charisma': 10,
            'club_id': None,
            'exp': 0,
            'hp': 100,
            'tusd': 1000,
            'inventory': {},
            'level': 1,
            'reputation': 0,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        # Create player item with proper key structure and default values
        item = {
            'PK': f"PLAYER#{user_id}",
            'SK': 'PROFILE',
            'user_id': user_id,
            'name': name,
            **defaults,  # Add default values
            **kwargs     # Override defaults with any provided values
        }
        # Convert numeric values to Decimal
        for key, value in item.items():
            if isinstance(value, (int, float)):
                item[key] = decimal.Decimal(str(value))
            elif key == 'inventory' and isinstance(value, dict):
                item[key] = json.dumps(value)
        await table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return False

@handle_dynamo_error
async def update_player(user_id: str, **kwargs) -> bool:
    """Update a player in DynamoDB."""
    if not user_id:
        return False
    try:
        table = get_table(TABLES['players'])
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                value = decimal.Decimal(str(value))
            update_expr += f"#{key} = :{key}, "
            expr_attr_values[f":{key}"] = value
        update_expr = update_expr[:-2]  # Remove trailing comma and space
        update_expr += ", last_updated = :last_updated"
        expr_attr_values[':last_updated'] = datetime.now().isoformat()
        
        # Add expression attribute names
        expr_attr_names = {f"#{key}": key for key in kwargs.keys()}
        
        # Update player
        await table.update_item(
            Key={
                'PK': f"PLAYER#{user_id}",
                'SK': 'PROFILE'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names
        )
        return True
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        return False

@handle_dynamo_error
async def get_all_players() -> List[Dict[str, Any]]:
    """Get all players from DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        response = await table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'PROFILE'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all players: {e}")
        return []

@handle_dynamo_error
async def get_top_players(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top players by level and experience."""
    try:
        players = await get_all_players()
        sorted_players = sorted(
            players,
            key=lambda x: (x.get('level', 0), x.get('exp', 0)),
            reverse=True
        )
        return sorted_players[:limit]
    except Exception as e:
        logger.error(f"Error getting top players: {e}")
        return []

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