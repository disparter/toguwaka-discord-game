"""
Item operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.items')

@handle_dynamo_error
async def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Get an item by its ID."""
    try:
        table = get_table('Itens')
        response = table.get_item(Key={'PK': f'ITEM#{item_id}', 'SK': 'INFO'})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {str(e)}")
        return None

@handle_dynamo_error
async def get_all_items() -> List[Dict[str, Any]]:
    """Get all items."""
    try:
        table = get_table('Itens')
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'INFO'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all items: {str(e)}")
        return []

@handle_dynamo_error
async def create_item(item_id: str, item_data: Dict[str, Any]) -> bool:
    """Create a new item."""
    try:
        table = get_table('Itens')
        
        # Convert numeric values to Decimal for DynamoDB compatibility
        for key, value in item_data.items():
            if isinstance(value, (int, float)):
                item_data[key] = Decimal(str(value))
        
        table.put_item(Item={
            'PK': f'ITEM#{item_id}',
            'SK': 'INFO',
            **item_data,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error creating item {item_id}: {str(e)}")
        return False

@handle_dynamo_error
async def update_item(item_id: str, item_data: Dict[str, Any]) -> bool:
    """Update an existing item."""
    try:
        table = get_table('Itens')
        
        # Get current item data
        current_item = await get_item(item_id)
        if not current_item:
            return False
            
        # Convert numeric values to Decimal
        for key, value in item_data.items():
            if isinstance(value, (int, float)):
                item_data[key] = Decimal(str(value))
        
        # Update item
        table.put_item(Item={
            **current_item,
            **item_data,
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {str(e)}")
        return False

@handle_dynamo_error
async def delete_item(item_id: str) -> bool:
    """Delete an item."""
    try:
        table = get_table('Itens')
        table.delete_item(Key={
            'PK': f'ITEM#{item_id}',
            'SK': 'INFO'
        })
        return True
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_items_by_type(item_type: str) -> List[Dict[str, Any]]:
    """Get all items of a specific type."""
    try:
        table = get_table('Itens')
        response = table.scan(
            FilterExpression='SK = :sk AND item_type = :type',
            ExpressionAttributeValues={
                ':sk': 'INFO',
                ':type': item_type
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting items of type {item_type}: {str(e)}")
        return []

@handle_dynamo_error
async def get_items_by_rarity(rarity: str) -> List[Dict[str, Any]]:
    """Get all items of a specific rarity."""
    try:
        table = get_table('Itens')
        response = table.scan(
            FilterExpression='SK = :sk AND rarity = :rarity',
            ExpressionAttributeValues={
                ':sk': 'INFO',
                ':rarity': rarity
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting items of rarity {rarity}: {str(e)}")
        return [] 