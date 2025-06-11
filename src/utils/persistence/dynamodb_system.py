"""
System operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.system')

@handle_dynamo_error
async def get_system_flag(flag_name: str) -> Optional[str]:
    """Get a system flag value."""
    try:
        table = get_table('SystemFlags')
        response = await table.get_item(
            Key={
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}'
            }
        )
        return response.get('Item', {}).get('value')
    except Exception as e:
        logger.error(f"Error getting system flag {flag_name}: {str(e)}")
        return None

@handle_dynamo_error
async def set_system_flag(flag_name: str, value: str, flag_type: str = 'system') -> bool:
    """Set a system flag value."""
    try:
        table = get_table('SystemFlags')
        item = {
            'PK': 'SYSTEM',
            'SK': f'FLAG#{flag_name}',
            'value': value,
            'flag_type': flag_type,
            'last_updated': datetime.now().isoformat()
        }
        
        # For daily events flags, add the date field
        if flag_name.startswith('daily_events_triggered_'):
            date_str = flag_name.replace('daily_events_triggered_', '')
            try:
                # Validate date format
                datetime.strptime(date_str, '%Y%m%d')
                item['date'] = date_str
                item['flag_type'] = 'daily_events'
            except ValueError:
                logger.warning(f"Invalid date format in flag {flag_name}")
                return False
        
        table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error setting system flag {flag_name}: {str(e)}")
        return False

@handle_dynamo_error
async def get_daily_events_flags() -> List[Dict[str, Any]]:
    """Get all daily events flags."""
    try:
        table = get_table('SystemFlags')
        response = table.scan(
            FilterExpression='PK = :pk AND begins_with(SK, :sk) AND flag_type = :type',
            ExpressionAttributeValues={
                ':pk': 'SYSTEM',
                ':sk': 'FLAG#daily_events_triggered_',
                ':type': 'daily_events'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting daily events flags: {str(e)}")
        return []

@handle_dynamo_error
async def delete_system_flag(flag_name: str) -> bool:
    """Delete a system flag."""
    try:
        table = get_table('SystemFlags')
        table.delete_item(
            Key={
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting system flag {flag_name}: {str(e)}")
        return False

@handle_dynamo_error
async def get_all_system_flags() -> List[Dict[str, Any]]:
    """Get all system flags."""
    try:
        table = get_table('SystemFlags')
        response = table.scan(
            FilterExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': 'SYSTEM'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all system flags: {str(e)}")
        return [] 