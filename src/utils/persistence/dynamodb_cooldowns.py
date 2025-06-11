"""
Cooldown operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.cooldowns')

@handle_dynamo_error
async def store_cooldown(user_id: str, command: str, expiry_time: datetime) -> bool:
    """Store a cooldown for a command."""
    try:
        table = get_table('Cooldowns')
        table.put_item(Item={
            'PK': f'PLAYER#{user_id}',
            'SK': f'COMMAND#{command}',
            'expiry_time': expiry_time.isoformat(),
            'command': command,
            'created_at': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error storing cooldown for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_cooldowns(user_id: str) -> Dict[str, datetime]:
    """Get all cooldowns for a player."""
    try:
        table = get_table('Cooldowns')
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'PLAYER#{user_id}'
            }
        )
        
        cooldowns = {}
        for item in response.get('Items', []):
            command = item['SK'].replace('COMMAND#', '')
            expiry_time = datetime.fromisoformat(item['expiry_time'])
            cooldowns[command] = expiry_time
            
        return cooldowns
    except Exception as e:
        logger.error(f"Error getting cooldowns for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def get_cooldown(user_id: str, command: str) -> Optional[datetime]:
    """Get cooldown for a specific command for a player."""
    try:
        table = get_table('Cooldowns')
        response = table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'COMMAND#{command}'
            }
        )
        
        item = response.get('Item')
        if item:
            return datetime.fromisoformat(item['expiry_time'])
        return None
    except Exception as e:
        logger.error(f"Error getting cooldown for player {user_id} command {command}: {str(e)}")
        return None

@handle_dynamo_error
async def clear_expired_cooldowns(user_id: Optional[str] = None) -> int:
    """
    Clear expired cooldowns from the database.
    
    Args:
        user_id: Optional user ID to clear cooldowns for a specific user only.
                 If None, clears all expired cooldowns.
    
    Returns:
        Number of cooldowns cleared
    """
    try:
        table = get_table('Cooldowns')
        now = datetime.now().isoformat()
        cleared_count = 0
        
        if user_id:
            # Clear expired cooldowns for specific user
            response = table.query(
                KeyConditionExpression='PK = :pk',
                FilterExpression='expiry_time < :now',
                ExpressionAttributeValues={
                    ':pk': f'PLAYER#{user_id}',
                    ':now': now
                }
            )
        else:
            # Clear all expired cooldowns
            response = table.scan(
                FilterExpression='expiry_time < :now',
                ExpressionAttributeValues={
                    ':now': now
                }
            )
        
        items = response.get('Items', [])
        for item in items:
            table.delete_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
            cleared_count += 1
        
        logger.info(f"Cleared {cleared_count} expired cooldowns" + (f" for user {user_id}" if user_id else ""))
        return cleared_count
        
    except Exception as e:
        logger.error(f"Error clearing expired cooldowns: {e}")
        return 0 