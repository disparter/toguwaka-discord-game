"""
Item usage tracking for DynamoDB.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.item_usage')

@handle_dynamo_error
async def track_item_usage(user_id: str, item_id: str, usage_type: str) -> bool:
    """
    Track item usage for limits.
    
    Args:
        user_id: ID of the player using the item
        item_id: ID of the item being used
        usage_type: Type of usage limit (daily, weekly, monthly)
        
    Returns:
        True if usage was tracked successfully
    """
    try:
        table = get_table('ItemUsage')
        now = datetime.now()
        
        # Calculate expiry based on usage type
        if usage_type == 'daily':
            expiry = now + timedelta(days=1)
        elif usage_type == 'weekly':
            expiry = now + timedelta(weeks=1)
        elif usage_type == 'monthly':
            expiry = now + timedelta(days=30)
        else:
            return False
            
        # Store usage record
        table.put_item(Item={
            'PK': f'PLAYER#{user_id}',
            'SK': f'ITEM#{item_id}#{usage_type}',
            'usage_count': 1,
            'first_used': now.isoformat(),
            'last_used': now.isoformat(),
            'expires_at': expiry.isoformat()
        })
        
        return True
    except Exception as e:
        logger.error(f"Error tracking item usage for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_item_usage_count(user_id: str, item_id: str, usage_type: str) -> int:
    """
    Get current usage count for an item.
    
    Args:
        user_id: ID of the player
        item_id: ID of the item
        usage_type: Type of usage limit (daily, weekly, monthly)
        
    Returns:
        Current usage count
    """
    try:
        table = get_table('ItemUsage')
        now = datetime.now()
        
        # Get usage record
        response = table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}#{usage_type}'
            }
        )
        
        item = response.get('Item')
        if not item:
            return 0
            
        # Check if usage record has expired
        expires_at = datetime.fromisoformat(item['expires_at'])
        if now > expires_at:
            return 0
            
        return item['usage_count']
    except Exception as e:
        logger.error(f"Error getting item usage count for player {user_id}: {str(e)}")
        return 0

@handle_dynamo_error
async def increment_item_usage(user_id: str, item_id: str, usage_type: str) -> bool:
    """
    Increment usage count for an item.
    
    Args:
        user_id: ID of the player
        item_id: ID of the item
        usage_type: Type of usage limit (daily, weekly, monthly)
        
    Returns:
        True if usage was incremented successfully
    """
    try:
        table = get_table('ItemUsage')
        now = datetime.now()
        
        # Update usage record
        table.update_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}#{usage_type}'
            },
            UpdateExpression='SET usage_count = usage_count + :inc, last_used = :now',
            ExpressionAttributeValues={
                ':inc': 1,
                ':now': now.isoformat()
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"Error incrementing item usage for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def clear_expired_usage_records() -> int:
    """
    Clear expired usage records.
    
    Returns:
        Number of records cleared
    """
    try:
        table = get_table('ItemUsage')
        now = datetime.now().isoformat()
        cleared_count = 0
        
        # Scan for expired records
        response = table.scan(
            FilterExpression='expires_at < :now',
            ExpressionAttributeValues={
                ':now': now
            }
        )
        
        # Delete expired records
        for item in response.get('Items', []):
            table.delete_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
            cleared_count += 1
            
        return cleared_count
    except Exception as e:
        logger.error(f"Error clearing expired usage records: {str(e)}")
        return 0 