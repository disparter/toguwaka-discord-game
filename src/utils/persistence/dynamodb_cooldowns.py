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
async def clear_expired_cooldowns() -> int:
    """
    Clear expired cooldowns.
    
    Returns:
        Number of records cleared
    """
    try:
        table = get_table('Cooldowns')
        now = datetime.now().isoformat()
        cleared_count = 0
        
        # Scan for expired records
        response = await table.scan(
            FilterExpression='expires_at < :now',
            ExpressionAttributeValues={
                ':now': now
            }
        )
        
        # Delete expired records
        for item in response.get('Items', []):
            await table.delete_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
            cleared_count += 1
            
        return cleared_count
    except Exception as e:
        logger.error(f"Error clearing expired cooldowns: {str(e)}")
        return 0 