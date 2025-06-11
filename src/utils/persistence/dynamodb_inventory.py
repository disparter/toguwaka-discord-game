"""
Inventory operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.inventory')

@handle_dynamo_error
async def get_player_inventory(user_id: str) -> Dict[str, Any]:
    """Get a player's inventory."""
    try:
        table = get_table('Inventario')
        response = table.scan(
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

@handle_dynamo_error
async def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add an item to a player's inventory."""
    try:
        table = get_table('Inventario')
        
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
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimal(v) for v in obj]
            return obj

        item_data_with_id = convert_floats_to_decimal(item_data_with_id)

        table.put_item(Item={
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

@handle_dynamo_error
async def remove_item_from_inventory(user_id: str, item_id: str) -> bool:
    """Remove an item from a player's inventory."""
    try:
        table = get_table('Inventario')
        table.delete_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error removing item from inventory for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def update_item_quantity(user_id: str, item_id: str, quantity: int) -> bool:
    """Update the quantity of an item in a player's inventory."""
    try:
        table = get_table('Inventario')
        table.update_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}'
            },
            UpdateExpression='SET item_data.quantity = :quantity, last_updated = :now',
            ExpressionAttributeValues={
                ':quantity': quantity,
                ':now': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error updating item quantity for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_item_details(user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific item in a player's inventory."""
    try:
        table = get_table('Inventario')
        response = table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}'
            }
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting item details for player {user_id}: {str(e)}")
        return None 