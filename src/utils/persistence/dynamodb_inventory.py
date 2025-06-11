"""
Inventory operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table, TABLES
from utils.item_effects import ItemEffectHandler

logger = get_logger('tokugawa_bot.inventory')

@handle_dynamo_error
async def get_player_inventory(user_id: str) -> List[Dict[str, Any]]:
    """
    Get a player's inventory.
    
    Args:
        user_id: The player's user ID
        
    Returns:
        List of items in player's inventory
    """
    try:
        table = get_table(TABLES['inventory'])
        response = await table.get_item(
            Key={'user_id': user_id}
        )
        
        if 'Item' not in response:
            return []
            
        return response['Item'].get('items', [])
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {str(e)}")
        return []

@handle_dynamo_error
async def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any], quantity: int = 1) -> bool:
    """
    Add an item to a player's inventory.
    
    Args:
        user_id: The player's user ID
        item_id: The ID of the item to add
        item_data: The item data
        quantity: The quantity to add (default: 1)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table = get_table(TABLES['inventory'])
        
        # Get current inventory
        response = await table.get_item(
            Key={'user_id': user_id}
        )
        
        current_items = []
        if 'Item' in response:
            current_items = response['Item'].get('items', [])
            
        # Check if item already exists
        item_exists = False
        for item in current_items:
            if item['item_id'] == item_id:
                item['quantity'] += quantity
                item_exists = True
                break
                
        if not item_exists:
            # Add new item
            current_items.append({
                'item_id': item_id,
                'item_data': item_data,
                'quantity': quantity
            })
            
        # Update inventory
        await table.put_item(
            Item={
                'user_id': user_id,
                'items': current_items
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Error adding item to inventory for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def remove_item_from_inventory(user_id: str, item_id: str, quantity: int = 1) -> bool:
    """
    Remove an item from a player's inventory.
    
    Args:
        user_id: The player's user ID
        item_id: The ID of the item to remove
        quantity: The quantity to remove (default: 1)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table = get_table(TABLES['inventory'])
        
        # Get current inventory
        response = await table.get_item(
            Key={'user_id': user_id}
        )
        
        if 'Item' not in response:
            logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
            return False
            
        current_items = response['Item'].get('items', [])
        
        # Find and update item
        for item in current_items:
            if item['item_id'] == item_id:
                if item['quantity'] < quantity:
                    logger.warning(f"Not enough quantity of item {item_id} in player {user_id}'s inventory")
                    return False
                    
                item['quantity'] -= quantity
                
                # Remove item if quantity is 0
                if item['quantity'] <= 0:
                    current_items.remove(item)
                    
                # Update inventory
                await table.put_item(
                    Item={
                        'user_id': user_id,
                        'items': current_items
                    }
                )
                
                return True
                
        logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
        return False
    except Exception as e:
        logger.error(f"Error removing item from inventory for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def use_item(user_id: str, item_id: str) -> bool:
    """
    Use an item from inventory.
    
    Args:
        user_id: The player's user ID
        item_id: The ID of the item to use
        
    Returns:
        True if successful, False otherwise
    """
    try:
        table = get_table(TABLES['inventory'])
        
        # Get current inventory
        response = await table.get_item(
            Key={'user_id': user_id}
        )
        
        if 'Item' not in response:
            logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
            return False
            
        current_items = response['Item'].get('items', [])
        
        # Find item
        for item in current_items:
            if item['item_id'] == item_id:
                # Apply item effects
                effect_handler = ItemEffectHandler()
                success = await effect_handler.apply_effects(user_id, item['item_data'])
                
                if not success:
                    return False
                    
                # Remove item after use
                return await remove_item_from_inventory(user_id, item_id)
                
        logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
        return False
    except Exception as e:
        logger.error(f"Error using item {item_id} for player {user_id}: {str(e)}")
        return False

async def get_inventory(user_id: int) -> Dict[str, Any]:
    """
    Get a player's inventory from DynamoDB.
    
    Args:
        user_id: The player's user ID
        
    Returns:
        The player's inventory data
    """
    try:
        # Get the table
        table = await get_table(TABLES['inventory'])
        
        # Get the inventory
        response = await table.get_item(
            Key={
                'user_id': user_id
            }
        )
        
        # Return the inventory data
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {e}")
        return {} 