"""
Club operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.clubs')

@handle_dynamo_error
async def get_club(club_id: str) -> Optional[Dict[str, Any]]:
    """Get club data from database."""
    try:
        table = get_table('Clubes')
        response = await table.get_item(Key={'PK': f'CLUB#{club_id}', 'SK': 'INFO'})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {str(e)}")
        return None

@handle_dynamo_error
async def get_all_clubs() -> List[Dict[str, Any]]:
    """Get all clubs from database."""
    try:
        table = get_table('Clubes')
        response = table.scan(
            FilterExpression='begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':sk': 'INFO'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all clubs: {str(e)}")
        return []

@handle_dynamo_error
async def get_club_members(club_id: str) -> List[Dict[str, Any]]:
    """Get all members of a club."""
    try:
        table = get_table('Clubes')
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'CLUB#{club_id}',
                ':sk': 'MEMBER#'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting members for club {club_id}: {str(e)}")
        return []

@handle_dynamo_error
async def create_club(club_id: str, name: str, description: str, leader_id: str, **kwargs) -> bool:
    """Create a new club."""
    try:
        table = get_table('Clubes')
        
        # Convert numeric values to Decimal
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                kwargs[key] = Decimal(str(value))
        
        # Create club info
        club_data = {
            'PK': f'CLUB#{club_id}',
            'SK': 'INFO',
            'name': name,
            'description': description,
            'leader_id': leader_id,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            **kwargs
        }
        
        # Add leader as first member
        member_data = {
            'PK': f'CLUB#{club_id}',
            'SK': f'MEMBER#{leader_id}',
            'joined_at': datetime.now().isoformat(),
            'role': 'leader'
        }
        
        # Use batch write to add both items
        with table.batch_writer() as batch:
            batch.put_item(Item=club_data)
            batch.put_item(Item=member_data)
            
        return True
    except Exception as e:
        logger.error(f"Error creating club {club_id}: {str(e)}")
        return False

@handle_dynamo_error
async def update_club(club_id: str, **kwargs) -> bool:
    """Update club data."""
    try:
        table = get_table('Clubes')
        
        # Get current club data
        current_club = await get_club(club_id)
        if not current_club:
            return False
            
        # Convert numeric values to Decimal
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                kwargs[key] = Decimal(str(value))
        
        # Update club
        table.put_item(Item={
            **current_club,
            **kwargs,
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error updating club {club_id}: {str(e)}")
        return False

@handle_dynamo_error
async def add_member(club_id: str, user_id: str, role: str = 'member') -> bool:
    """Add a member to a club."""
    try:
        table = get_table('Clubes')
        
        # Check if club exists
        club = await get_club(club_id)
        if not club:
            return False
            
        # Add member
        table.put_item(Item={
            'PK': f'CLUB#{club_id}',
            'SK': f'MEMBER#{user_id}',
            'joined_at': datetime.now().isoformat(),
            'role': role
        })
        return True
    except Exception as e:
        logger.error(f"Error adding member {user_id} to club {club_id}: {str(e)}")
        return False

@handle_dynamo_error
async def remove_member(club_id: str, user_id: str) -> bool:
    """Remove a member from a club."""
    try:
        table = get_table('Clubes')
        
        # Check if club exists
        club = await get_club(club_id)
        if not club:
            return False
            
        # Remove member
        table.delete_item(Key={
            'PK': f'CLUB#{club_id}',
            'SK': f'MEMBER#{user_id}'
        })
        return True
    except Exception as e:
        logger.error(f"Error removing member {user_id} from club {club_id}: {str(e)}")
        return False

@handle_dynamo_error
async def update_member_role(club_id: str, user_id: str, new_role: str) -> bool:
    """Update a member's role in a club."""
    try:
        table = get_table('Clubes')
        
        # Check if club exists
        club = await get_club(club_id)
        if not club:
            return False
            
        # Update member role
        table.put_item(Item={
            'PK': f'CLUB#{club_id}',
            'SK': f'MEMBER#{user_id}',
            'role': new_role,
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error updating role for member {user_id} in club {club_id}: {str(e)}")
        return False

@handle_dynamo_error
async def delete_club(club_id: str) -> bool:
    """Delete a club and all its members."""
    try:
        table = get_table('Clubes')
        
        # Get all club items (info and members)
        response = table.scan(
            FilterExpression='begins_with(PK, :pk)',
            ExpressionAttributeValues={
                ':pk': f'CLUB#{club_id}'
            }
        )
        
        # Delete all items
        with table.batch_writer() as batch:
            for item in response.get('Items', []):
                batch.delete_item(Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                })
                
        return True
    except Exception as e:
        logger.error(f"Error deleting club {club_id}: {str(e)}")
        return False
