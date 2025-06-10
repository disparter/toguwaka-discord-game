import logging
from datetime import datetime
from utils.persistence.dynamodb import (
    get_table,
    put_item,
    get_item,
    query_items,
    scan_items,
    update_item,
    delete_item,
    TABLES, handle_dynamo_error, DynamoDBOperationError
)

logger = logging.getLogger('tokugawa_bot')

@handle_dynamo_error
async def get_club(club_id):
    """Get club data from DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        # Try first with the PK/SK format as it's the correct schema
        try:
            response = await table.get_item(
                Key={
                    'PK': f"CLUB#{club_id}",
                    'SK': 'INFO'
                }
            )
            if 'Item' in response:
                item = response['Item']
                club = {
                    'name': item.get('name', ''),
                    'description': item.get('description', ''),
                    'leader_id': item.get('leader_id', ''),
                    'reputacao': item.get('reputacao', 0)
                }
                return club
        except Exception as primary_error:
            # Log error from primary attempt
            logger.warning(f"Error getting club {club_id} with PK/SK format: {primary_error}")

        # If not found or error occurred, try with NomeClube as fallback for backward compatibility
        try:
            response = await table.get_item(
                Key={
                    'NomeClube': str(club_id)
                }
            )
            if 'Item' in response:
                item = response['Item']
                club = {
                    'name': item.get('NomeClube', ''),
                    'description': item.get('descricao', ''),
                    'leader_id': item.get('lider_id', ''),
                    'reputacao': item.get('reputacao', 0)
                }
                return club
        except Exception as fallback_error:
            # Ignore errors from the fallback attempt
            logger.warning(f"Error getting club {club_id} with NomeClube format: {fallback_error}")
            pass


        return None
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get club: {e}") from e

@handle_dynamo_error
async def get_all_clubs():
    """Get all clubs from DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        client = table.meta.client
        response = await client.scan(
            TableName=TABLES['clubs']
        )
        clubs = []
        if 'Items' in response:
            for item in response['Items']:
                club = {
                    'PK': item.get('PK', ''),
                    'name': item.get('name', ''),
                    'description': item.get('description', ''),
                    'leader_id': item.get('leader_id', ''),
                    'reputacao': item.get('reputacao', 0)
                }
                clubs.append(club)
        sorted_clubs = sorted(clubs, key=lambda x: x['name'])
        return sorted_clubs
    except Exception as e:
        logger.error(f"Error getting all clubs: {e}")
        raise DynamoDBOperationError(f"Failed to get all clubs: {e}") from e

@handle_dynamo_error
async def create_club(club_id, name, description, leader_id):
    """Create a new club in DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        # Create club with the correct PK/SK schema
        club_item = {
            'PK': f"CLUB#{club_id}",
            'SK': 'INFO',
            'name': name,
            'description': description,
            'leader_id': leader_id,
            'reputacao': 0,
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        logger.info(f"Creating club with item: {club_item}")
        await table.put_item(Item=club_item)

        # For backward compatibility, also create with the old schema
        try:
            old_format_item = {
                'NomeClube': name,
                'descricao': description,
                'lider_id': leader_id,
                'reputacao': 0,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            await table.put_item(Item=old_format_item)
        except Exception as compat_error:
            logger.warning(f"Error creating club with old format: {compat_error}")

        return True
    except Exception as e:
        logger.error(f"Error creating club: {e}")
        return False

@handle_dynamo_error
async def get_top_clubs_by_activity(week=None, year=None, limit=3):
    """Get top clubs by activity points for a specific week."""
    try:
        if week is None or year is None:
            now = datetime.now()
            year, week, _ = now.isocalendar()
        activities_table = get_table(TABLES['club_activities'])
        clubs_table = get_table(TABLES['clubs'])
        response = await activities_table.query(
            IndexName='week-year-index',
            KeyConditionExpression='week = :week AND year = :year',
            ExpressionAttributeValues={
                ':week': week,
                ':year': year
            }
        )
        club_points = {}
        if 'Items' in response:
            for item in response['Items']:
                club_id = item.get('club_id')
                points = item.get('points', 0)
                if club_id in club_points:
                    club_points[club_id] += points
                else:
                    club_points[club_id] = points
        top_clubs = []
        for club_id, total_points in sorted(club_points.items(), key=lambda x: x[1], reverse=True)[:limit]:
            # Try with PK/SK format first
            try:
                club_response = await clubs_table.get_item(
                    Key={
                        'PK': f"CLUB#{club_id}",
                        'SK': 'INFO'
                    }
                )
                if 'Item' in club_response:
                    club = club_response['Item']
                    top_clubs.append({
                        'name': club.get('name', ''),
                        'description': club.get('description', ''),
                        'leader_id': club.get('leader_id', ''),
                        'reputacao': club.get('reputacao', 0),
                        'total_points': total_points
                    })
                    continue
            except Exception as e:
                logger.warning(f"Error getting club {club_id} with PK/SK format in top clubs: {e}")

            # Fallback to NomeClube format
            try:
                club_response = await clubs_table.get_item(Key={'NomeClube': club_id})
                if 'Item' in club_response:
                    club = club_response['Item']
                    top_clubs.append({
                        'name': club.get('NomeClube', ''),
                        'description': club.get('descricao', ''),
                        'leader_id': club.get('lider_id', ''),
                        'reputacao': club.get('reputacao', 0),
                        'total_points': total_points
                    })
            except Exception as e:
                logger.warning(f"Error getting club {club_id} with NomeClube format in top clubs: {e}")
        return top_clubs
    except Exception as e:
        logger.error(f"Error getting top clubs by activity: {e}")
        return []

@handle_dynamo_error
async def record_club_activity(user_id, activity_type, points=1):
    """Record a club activity for a player's club."""
    try:
        players_table = get_table(TABLES['players'])
        player_response = await players_table.get_item(Key={'user_id': user_id})
        if 'Item' not in player_response:
            logger.info(f"Player {user_id} not found, skipping activity recording")
            return False
        player = player_response['Item']
        club_id = player.get('club_id')
        if not club_id:
            logger.info(f"Player {user_id} has no club, skipping activity recording")
            return False
        now = datetime.now()
        year, week, _ = now.isocalendar()
        activities_table = get_table(TABLES['club_activities'])
        activity_id = f"{club_id}#{user_id}#{activity_type}#{week}#{year}"
        await activities_table.put_item(
            Item={
                'PK': f"CLUB#{club_id}",
                'SK': f"ACTIVITY#{activity_id}",
                'club_id': club_id,
                'user_id': user_id,
                'activity_type': activity_type,
                'points': points,
                'week': week,
                'year': year,
                'created_at': now.isoformat()
            }
        )
        logger.info(f"Recorded {activity_type} activity for club {club_id} by player {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error recording club activity: {e}")
        return False
