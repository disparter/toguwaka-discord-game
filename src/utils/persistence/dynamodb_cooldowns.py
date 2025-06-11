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
        await table.put_item(Item={
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
async def get_cooldowns(user_id: str = None) -> Dict[str, Dict[str, datetime]]:
    """Get all cooldowns for a player or all players."""
    try:
        table = get_table('Cooldowns')
        if user_id:
            response = await table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'PLAYER#{user_id}'
                }
            )
        else:
            response = await table.scan()
        
        cooldowns = {}
        for item in response.get('Items', []):
            user_id = item['PK'].replace('PLAYER#', '')
            command = item['SK'].replace('COMMAND#', '')
            expiry_time = datetime.fromisoformat(item['expiry_time'])
            
            if user_id not in cooldowns:
                cooldowns[user_id] = {}
            cooldowns[user_id][command] = expiry_time
            
        return cooldowns
    except Exception as e:
        logger.error(f"Error getting cooldowns: {str(e)}")
        return {}

@handle_dynamo_error
async def get_cooldown(user_id: str, command: str) -> Optional[datetime]:
    """Get cooldown for a specific command for a player."""
    try:
        table = get_table('Cooldowns')
        response = await table.get_item(
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
async def clear_expired_cooldowns(user_id: str = None) -> int:
    """Clear expired cooldowns from the database."""
    try:
        table = get_table('Cooldowns')
        now = datetime.now()
        cleared = 0

        if user_id:
            # Get cooldowns for specific user
            response = await table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'PLAYER#{user_id}'
                }
            )
            items = response.get('Items', [])
        else:
            # Get all cooldowns
            response = await table.scan()
            items = response.get('Items', [])

        # Delete expired cooldowns
        for item in items:
            expiry_time = datetime.fromisoformat(item['expiry_time'])
            if expiry_time < now:
                await table.delete_item(
                    Key={
                        'PK': item['PK'],
                        'SK': item['SK']
                    }
                )
                cleared += 1

        return cleared
    except Exception as e:
        logger.error(f"Error clearing expired cooldowns: {str(e)}")
        return 0 