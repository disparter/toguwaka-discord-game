"""
Inventory operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table
from utils.item_effects import ItemEffectHandler

logger = get_logger('tokugawa_bot.inventory')

@handle_dynamo_error
async def get_player_inventory(user_id: str) -> List[Dict[str, Any]]:
    """
    Get a player's inventory.
    
    Args:
        user_id: ID of the player
        
    Returns:
        List of items in player's inventory
    """
    try:
        table = get_table('Inventory')
        response = table.query(
            KeyConditionExpression='JogadorID = :user_id',
            ExpressionAttributeValues={
                ':user_id': f'PLAYER#{user_id}'
            }
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {str(e)}")
        return []

@handle_dynamo_error
async def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any], quantity: int = 1) -> bool:
    """
    Add an item to a player's inventory.
    
    Args:
        user_id: ID of the player
        item_id: ID of the item to add
        item_data: Data for the item
        quantity: Quantity to add
        
    Returns:
        True if item was added successfully
    """
    try:
        table = get_table('Inventory')
        
        # Check if item already exists
        response = table.get_item(
            Key={
                'JogadorID': f'PLAYER#{user_id}',
                'ItemID': item_id
            }
        )
        
        item = response.get('Item')
        if item:
            # Update quantity if item exists
            table.update_item(
                Key={
                    'JogadorID': f'PLAYER#{user_id}',
                    'ItemID': item_id
                },
                UpdateExpression='SET quantity = quantity + :qty',
                ExpressionAttributeValues={
                    ':qty': quantity
                }
            )
        else:
            # Add new item
            table.put_item(Item={
                'JogadorID': f'PLAYER#{user_id}',
                'ItemID': item_id,
                'item_data': item_data,
                'quantity': quantity,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            
        return True
    except Exception as e:
        logger.error(f"Error adding item to inventory for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def remove_item_from_inventory(user_id: str, item_id: str, quantity: int = 1) -> bool:
    """
    Remove an item from a player's inventory.
    
    Args:
        user_id: ID of the player
        item_id: ID of the item to remove
        quantity: Quantity to remove
        
    Returns:
        True if item was removed successfully
    """
    try:
        table = get_table('Inventory')
        
        # Get current item
        response = table.get_item(
            Key={
                'JogadorID': f'PLAYER#{user_id}',
                'ItemID': item_id
            }
        )
        
        item = response.get('Item')
        if not item:
            logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
            return False
            
        current_quantity = item.get('quantity', 0)
        if current_quantity < quantity:
            logger.warning(f"Not enough quantity of item {item_id} in player {user_id}'s inventory")
            return False
            
        if current_quantity == quantity:
            # Remove item completely
            table.delete_item(
                Key={
                    'JogadorID': f'PLAYER#{user_id}',
                    'ItemID': item_id
                }
            )
        else:
            # Update quantity
            table.update_item(
                Key={
                    'JogadorID': f'PLAYER#{user_id}',
                    'ItemID': item_id
                },
                UpdateExpression='SET quantity = quantity - :qty, last_updated = :now',
                ExpressionAttributeValues={
                    ':qty': quantity,
                    ':now': datetime.now().isoformat()
                }
            )
            
        return True
    except Exception as e:
        logger.error(f"Error removing item from inventory for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def use_item(user_id: str, item_id: str) -> bool:
    """
    Use an item from inventory.
    
    Args:
        user_id: ID of the player
        item_id: ID of the item to use
        
    Returns:
        True if item was used successfully
    """
    try:
        table = get_table('Inventory')
        
        # Get item
        response = table.get_item(
            Key={
                'JogadorID': f'PLAYER#{user_id}',
                'ItemID': item_id
            }
        )
        
        item = response.get('Item')
        if not item:
            logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
            return False
            
        item_data = item.get('item_data', {})
        if not item_data.get('usable', False):
            logger.warning(f"Item {item_id} is not usable")
            return False
            
        # Apply effect
        effect_type = item_data.get('effect_type')
        effect_data = item_data.get('effect_data', {})
        
        if not effect_type or not effect_data:
            logger.warning(f"Item {item_id} has no effect data")
            return False
            
        success = await ItemEffectHandler.apply_effect(user_id, item_id, effect_type, effect_data)
        if not success:
            return False
            
        # Remove item if consumable
        if item_data.get('consumable', True):
            return await remove_item_from_inventory(user_id, item_id)
            
        return True
    except Exception as e:
        logger.error(f"Error using item for player {user_id}: {str(e)}")
        return False 