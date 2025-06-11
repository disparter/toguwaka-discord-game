"""
Scheduled events operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.scheduled_events')

@handle_dynamo_error
async def create_scheduled_event(event_id: str, event_data: Dict[str, Any]) -> bool:
    """Create a new scheduled event."""
    try:
        table = get_table('Events')
        
        # Convert numeric values to Decimal
        for key, value in event_data.items():
            if isinstance(value, (int, float)):
                event_data[key] = Decimal(str(value))
                
        # Add timestamps
        event_data.update({
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        
        table.put_item(Item={
            'PK': f'EVENT#{event_id}',
            'SK': f'SCHEDULED#{event_id}',
            **event_data
        })
        return True
    except Exception as e:
        logger.error(f"Error creating scheduled event {event_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_scheduled_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Get a scheduled event by its ID."""
    try:
        table = get_table('Events')
        response = table.get_item(Key={
            'PK': f'EVENT#{event_id}',
            'SK': f'SCHEDULED#{event_id}'
        })
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting scheduled event {event_id}: {str(e)}")
        return None

@handle_dynamo_error
async def get_upcoming_events(limit: int = 10) -> List[Dict[str, Any]]:
    """Get upcoming scheduled events."""
    try:
        table = get_table('Events')
        now = datetime.now().isoformat()
        
        response = table.scan(
            FilterExpression='begins_with(SK, :sk) AND start_time > :now',
            ExpressionAttributeValues={
                ':sk': 'SCHEDULED#',
                ':now': now
            }
        )
        
        events = response.get('Items', [])
        sorted_events = sorted(events, key=lambda x: x['start_time'])[:limit]
        return sorted_events
    except Exception as e:
        logger.error(f"Error getting upcoming events: {str(e)}")
        return []

@handle_dynamo_error
async def get_active_events() -> List[Dict[str, Any]]:
    """Get currently active events."""
    try:
        table = get_table('Events')
        now = datetime.now().isoformat()
        
        response = table.scan(
            FilterExpression='begins_with(SK, :sk) AND start_time <= :now AND end_time > :now',
            ExpressionAttributeValues={
                ':sk': 'SCHEDULED#',
                ':now': now
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting active events: {str(e)}")
        return []

@handle_dynamo_error
async def update_scheduled_event(event_id: str, **kwargs) -> bool:
    """Update a scheduled event."""
    try:
        table = get_table('Events')
        
        # Get current event data
        current_event = await get_scheduled_event(event_id)
        if not current_event:
            return False
            
        # Convert numeric values to Decimal
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                kwargs[key] = Decimal(str(value))
        
        # Update event
        table.put_item(Item={
            **current_event,
            **kwargs,
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error updating scheduled event {event_id}: {str(e)}")
        return False

@handle_dynamo_error
async def delete_scheduled_event(event_id: str) -> bool:
    """Delete a scheduled event."""
    try:
        table = get_table('Events')
        table.delete_item(Key={
            'PK': f'EVENT#{event_id}',
            'SK': f'SCHEDULED#{event_id}'
        })
        return True
    except Exception as e:
        logger.error(f"Error deleting scheduled event {event_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_events_by_type(event_type: str) -> List[Dict[str, Any]]:
    """Get all events of a specific type."""
    try:
        table = get_table('Events')
        response = table.scan(
            FilterExpression='begins_with(SK, :sk) AND event_type = :type',
            ExpressionAttributeValues={
                ':sk': 'SCHEDULED#',
                ':type': event_type
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting events of type {event_type}: {str(e)}")
        return []

@handle_dynamo_error
async def get_events_by_creator(creator_id: str) -> List[Dict[str, Any]]:
    """Get all events created by a specific user."""
    try:
        table = get_table('Events')
        response = table.scan(
            FilterExpression='begins_with(SK, :sk) AND creator_id = :creator',
            ExpressionAttributeValues={
                ':sk': 'SCHEDULED#',
                ':creator': creator_id
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting events by creator {creator_id}: {str(e)}")
        return [] 