"""
Club activities operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.club_activities')

@handle_dynamo_error
async def record_club_activity(club_id: str, user_id: str, activity_type: str, points: int = 1) -> bool:
    """Record a club activity."""
    try:
        table = get_table('AtividadesClube')
        now = datetime.now()
        year, week, _ = now.isocalendar()
        
        activity_id = f"{club_id}#{user_id}#{activity_type}#{week}#{year}"
        table.put_item(Item={
            'PK': f'CLUB#{club_id}',
            'SK': f'ACTIVITY#{activity_id}',
            'club_id': club_id,
            'user_id': user_id,
            'activity_type': activity_type,
            'points': Decimal(str(points)),
            'week': week,
            'year': year,
            'created_at': now.isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error recording club activity: {str(e)}")
        return False

@handle_dynamo_error
async def get_club_activities(club_id: str, week: Optional[int] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get activities for a club in a specific week."""
    try:
        if week is None or year is None:
            now = datetime.now()
            year, week, _ = now.isocalendar()
            
        table = get_table('AtividadesClube')
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            FilterExpression='week = :week AND year = :year',
            ExpressionAttributeValues={
                ':pk': f'CLUB#{club_id}',
                ':sk': 'ACTIVITY#',
                ':week': week,
                ':year': year
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting club activities: {str(e)}")
        return []

@handle_dynamo_error
async def get_user_activities(user_id: str, club_id: str) -> List[Dict[str, Any]]:
    """Get all activities for a user in a club."""
    try:
        table = get_table('AtividadesClube')
        response = table.scan(
            FilterExpression='club_id = :club AND user_id = :user',
            ExpressionAttributeValues={
                ':club': club_id,
                ':user': user_id
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting user activities: {str(e)}")
        return []

@handle_dynamo_error
async def get_top_clubs_by_activity(week: Optional[int] = None, year: Optional[int] = None, limit: int = 3) -> List[Dict[str, Any]]:
    """Get top clubs by activity points for a specific week."""
    try:
        if week is None or year is None:
            now = datetime.now()
            year, week, _ = now.isocalendar()
            
        table = get_table('AtividadesClube')
        response = table.scan(
            FilterExpression='week = :week AND year = :year',
            ExpressionAttributeValues={
                ':week': week,
                ':year': year
            }
        )
        
        # Calculate total points per club
        club_points = {}
        for item in response.get('Items', []):
            club_id = item['club_id']
            points = item['points']
            if club_id in club_points:
                club_points[club_id] += points
            else:
                club_points[club_id] = points
                
        # Sort clubs by points
        sorted_clubs = sorted(
            club_points.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        # Get club details
        from utils.persistence.dynamodb_clubs import get_club
        top_clubs = []
        for club_id, total_points in sorted_clubs:
            club = await get_club(club_id)
            if club:
                top_clubs.append({
                    **club,
                    'total_points': float(total_points)
                })
                
        return top_clubs
    except Exception as e:
        logger.error(f"Error getting top clubs by activity: {str(e)}")
        return []

@handle_dynamo_error
async def get_activity_stats(club_id: str) -> Dict[str, Any]:
    """Get activity statistics for a club."""
    try:
        table = get_table('AtividadesClube')
        response = table.scan(
            FilterExpression='club_id = :club',
            ExpressionAttributeValues={
                ':club': club_id
            }
        )
        
        activities = response.get('Items', [])
        if not activities:
            return {}
            
        stats = {
            'total_activities': len(activities),
            'total_points': sum(float(a['points']) for a in activities),
            'activity_types': {},
            'weekly_activity': {},
            'user_activity': {}
        }
        
        for activity in activities:
            # Count by activity type
            activity_type = activity['activity_type']
            if activity_type not in stats['activity_types']:
                stats['activity_types'][activity_type] = 0
            stats['activity_types'][activity_type] += 1
            
            # Count by week
            week_key = f"{activity['year']}-W{activity['week']}"
            if week_key not in stats['weekly_activity']:
                stats['weekly_activity'][week_key] = 0
            stats['weekly_activity'][week_key] += float(activity['points'])
            
            # Count by user
            user_id = activity['user_id']
            if user_id not in stats['user_activity']:
                stats['user_activity'][user_id] = 0
            stats['user_activity'][user_id] += float(activity['points'])
            
        return stats
    except Exception as e:
        logger.error(f"Error getting activity stats: {str(e)}")
        return {} 