"""
Market operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.market')

@handle_dynamo_error
async def get_market_items() -> List[Dict[str, Any]]:
    """Get all items in the market."""
    try:
        table = get_table('Mercado')
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting market items: {str(e)}")
        return []

@handle_dynamo_error
async def add_market_item(item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add an item to the market."""
    try:
        table = get_table('Mercado')
        table.put_item(Item={
            'PK': f'ITEM#{item_id}',
            'SK': 'MARKET',
            **item_data,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error adding market item {item_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_market_listing(item_id: str, seller_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific market listing."""
    try:
        table = get_table('Mercado')
        response = table.get_item(
            Key={
                'PK': f'ITEM#{item_id}',
                'SK': f'SELLER#{seller_id}'
            }
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting market listing for item {item_id}: {str(e)}")
        return None

@handle_dynamo_error
async def list_item_for_sale(item_id: str, seller_id: str, price: float) -> bool:
    """List an item for sale in the market."""
    try:
        table = get_table('Mercado')
        table.put_item(Item={
            'PK': f'ITEM#{item_id}',
            'SK': f'SELLER#{seller_id}',
            'price': price,
            'seller_id': seller_id,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error listing item {item_id} for sale: {str(e)}")
        return False

@handle_dynamo_error
async def remove_market_listing(item_id: str, seller_id: str) -> bool:
    """Remove an item from the market."""
    try:
        table = get_table('Mercado')
        table.delete_item(
            Key={
                'PK': f'ITEM#{item_id}',
                'SK': f'SELLER#{seller_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error removing market listing for item {item_id}: {str(e)}")
        return False

@handle_dynamo_error
async def update_market_price(item_id: str, seller_id: str, new_price: float) -> bool:
    """Update the price of a market listing."""
    try:
        table = get_table('Mercado')
        table.update_item(
            Key={
                'PK': f'ITEM#{item_id}',
                'SK': f'SELLER#{seller_id}'
            },
            UpdateExpression='SET price = :price, last_updated = :now',
            ExpressionAttributeValues={
                ':price': new_price,
                ':now': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error updating market price for item {item_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_seller_listings(seller_id: str) -> List[Dict[str, Any]]:
    """Get all market listings for a specific seller."""
    try:
        table = get_table('Mercado')
        response = table.scan(
            FilterExpression='seller_id = :seller_id',
            ExpressionAttributeValues={
                ':seller_id': seller_id
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting seller listings for {seller_id}: {str(e)}")
        return [] 