"""
Inventory operations for DynamoDB.
"""

import os
import logging
import boto3
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table, TABLES
from utils.item_effects import ItemEffectHandler

logger = logging.getLogger('tokugawa_bot.inventory')

# Initialize DynamoDB client
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def get_table(table_name: str):
    """Get DynamoDB table."""
    return dynamodb.Table(table_name)

class DynamoDBInventory:
    """Class for handling inventory data in DynamoDB."""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('Inventario')
    
    async def get_player_inventory(self, user_id: str) -> Dict[str, Any]:
        """Get player inventory from DynamoDB."""
        try:
            if not user_id:
                logger.warning("Empty user_id provided to get_player_inventory")
                return {}
            
            # Ensure user_id is a string
            user_id = str(user_id)
            
            # Get inventory data
            response = self.table.get_item(
                Key={
                    'PK': f'PLAYER#{user_id}',
                    'SK': 'INVENTORY'
                }
            )
            
            if 'Item' not in response:
                logger.info(f"No inventory found for player {user_id}, creating empty inventory")
                # Create empty inventory
                empty_inventory = {
                    'PK': f'PLAYER#{user_id}',
                    'SK': 'INVENTORY',
                    'items': {},
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                await self.table.put_item(Item=empty_inventory)
                return empty_inventory
            
            return response['Item']
            
        except Exception as e:
            logger.error(f"Error getting inventory for player {user_id}: {e}")
            return {}
    
    async def add_item_to_inventory(self, user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
        """Add item to player inventory."""
        try:
            # Get current inventory
            inventory = await self.get_player_inventory(user_id)
            
            # Update items
            items = inventory.get('items', {})
            if item_id in items:
                # Update quantity if item exists
                current_quantity = items[item_id].get('quantity', 0)
                items[item_id]['quantity'] = current_quantity + item_data.get('quantity', 1)
            else:
                # Add new item
                items[item_id] = {
                    'id': item_id,
                    'quantity': item_data.get('quantity', 1),
                    'added_at': datetime.now().isoformat(),
                    **item_data
                }
            
            # Update inventory
            inventory['items'] = items
            inventory['last_updated'] = datetime.now().isoformat()
            
            await self.table.put_item(Item=inventory)
            return True
        except Exception as e:
            logger.error(f"Error adding item to inventory for player {user_id}: {e}")
            return False
    
    async def remove_item_from_inventory(self, user_id: str, item_id: str) -> bool:
        """Remove item from player inventory."""
        try:
            # Get current inventory
            inventory = await self.get_player_inventory(user_id)
            
            # Update items
            items = inventory.get('items', {})
            if item_id in items:
                del items[item_id]
                inventory['items'] = items
                inventory['last_updated'] = datetime.now().isoformat()
                
                await self.table.put_item(Item=inventory)
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing item from inventory for player {user_id}: {e}")
            return False

# Create singleton instance
dynamodb_inventory = DynamoDBInventory()

# Export functions
get_player_inventory = dynamodb_inventory.get_player_inventory
add_item_to_inventory = dynamodb_inventory.add_item_to_inventory
remove_item_from_inventory = dynamodb_inventory.remove_item_from_inventory

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
            Key={
                'PK': f'USER#{user_id}',
                'SK': 'INVENTORY'
            }
        )
        
        if 'Item' not in response:
            logger.warning(f"Item {item_id} not found in player {user_id}'s inventory")
            return False
            
        current_items = response['Item'].get('items', {})
        
        # Find item
        if item_id in current_items:
            # Apply item effects
            effect_handler = ItemEffectHandler()
            success = await effect_handler.apply_effects(user_id, current_items[item_id])
            
            if not success:
                return False
                
            # Remove item after use
            del current_items[item_id]
            
            # Update inventory
            await table.put_item(
                Item={
                    'PK': f'USER#{user_id}',
                    'SK': 'INVENTORY',
                    'items': current_items
                }
            )
            
            return True
            
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