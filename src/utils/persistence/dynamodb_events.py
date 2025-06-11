"""
Event operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.events')

@handle_dynamo_error
async def store_event(event_id: str, name: str, description: str, event_type: str,
                     channel_id: str, message_id: str, start_time: datetime,
                     end_time: datetime, participants: List[str], data: Dict[str, Any],
                     completed: bool = False) -> bool:
    """Store an event in the database."""
    try:
        table = get_table('Eventos')
        table.put_item(Item={
            'PK': f'EVENT#{event_id}',
            'SK': f'TYPE#{event_type}',
            'name': name,
            'description': description,
            'channel_id': channel_id,
            'message_id': message_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'participants': participants,
            'data': data,
            'completed': completed,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error storing event {event_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Get an event by ID."""
    try:
        table = get_table('Eventos')
        response = table.get_item(
            Key={
                'PK': f'EVENT#{event_id}',
                'SK': 'EVENT'
            }
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {str(e)}")
        return None

@handle_dynamo_error
async def get_all_events() -> List[Dict[str, Any]]:
    """Get all events from database."""
    try:
        table = get_table('Eventos')
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': 'EVENT#',
                ':sk': 'EVENT'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all events: {str(e)}")
        return []

@handle_dynamo_error
async def get_active_events() -> List[Dict[str, Any]]:
    """Get all active (non-completed) events from database."""
    try:
        table = get_table('Eventos')
        current_time = datetime.now().isoformat()
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND SK = :sk AND #completed = :completed AND #end_time > :current_time',
            ExpressionAttributeValues={
                ':pk': 'EVENT#',
                ':sk': 'EVENT',
                ':completed': False,
                ':current_time': current_time
            },
            ExpressionAttributeNames={
                '#completed': 'completed',
                '#end_time': 'end_time'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting active events: {str(e)}")
        return []

@handle_dynamo_error
async def update_event(event_id: str, **kwargs) -> bool:
    """Update an event's data."""
    try:
        table = get_table('Eventos')
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for key, value in kwargs.items():
            if key in ['name', 'description', 'channel_id', 'message_id', 'start_time', 
                      'end_time', 'participants', 'data', 'completed']:
                update_expr += f"#{key} = :{key}, "
                expr_attr_values[f":{key}"] = value
                expr_attr_names[f"#{key}"] = key
        
        # Always update last_updated
        update_expr += "#last_updated = :last_updated"
        expr_attr_values[":last_updated"] = datetime.now().isoformat()
        expr_attr_names["#last_updated"] = "last_updated"
        
        table.update_item(
            Key={
                'PK': f'EVENT#{event_id}',
                'SK': 'EVENT'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names
        )
        return True
    except Exception as e:
        logger.error(f"Error updating event {event_id}: {str(e)}")
        return False

@handle_dynamo_error
async def delete_event(event_id: str) -> bool:
    """Delete an event from the database."""
    try:
        table = get_table('Eventos')
        table.delete_item(
            Key={
                'PK': f'EVENT#{event_id}',
                'SK': 'EVENT'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting event {event_id}: {str(e)}")
        return False 