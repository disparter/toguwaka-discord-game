"""
Vote operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.votes')

@handle_dynamo_error
async def add_vote(vote_id: str, user_id: str, vote_type: str, target_id: str, value: int) -> bool:
    """Add a vote to the database."""
    try:
        table = get_table('Votos')
        table.put_item(Item={
            'PK': f'VOTE#{vote_id}',
            'SK': f'USER#{user_id}',
            'vote_type': vote_type,
            'target_id': target_id,
            'value': Decimal(str(value)),
            'timestamp': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error adding vote: {str(e)}")
        return False

@handle_dynamo_error
async def get_vote_results(vote_id: str) -> Dict[str, Any]:
    """Get results for a specific vote."""
    try:
        table = get_table('Votos')
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'VOTE#{vote_id}'
            }
        )
        
        votes = response.get('Items', [])
        results = {
            'total_votes': len(votes),
            'positive_votes': sum(1 for v in votes if v['value'] > 0),
            'negative_votes': sum(1 for v in votes if v['value'] < 0),
            'neutral_votes': sum(1 for v in votes if v['value'] == 0),
            'details': votes
        }
        return results
    except Exception as e:
        logger.error(f"Error getting vote results for {vote_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def get_user_votes(user_id: str) -> List[Dict[str, Any]]:
    """Get all votes cast by a user."""
    try:
        table = get_table('Votos')
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': f'USER#{user_id}'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting votes for user {user_id}: {str(e)}")
        return []

@handle_dynamo_error
async def get_target_votes(target_id: str, vote_type: str) -> List[Dict[str, Any]]:
    """Get all votes for a specific target."""
    try:
        table = get_table('Votos')
        response = table.scan(
            FilterExpression='target_id = :target AND vote_type = :type',
            ExpressionAttributeValues={
                ':target': target_id,
                ':type': vote_type
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting votes for target {target_id}: {str(e)}")
        return []

@handle_dynamo_error
async def delete_vote(vote_id: str, user_id: str) -> bool:
    """Delete a specific vote."""
    try:
        table = get_table('Votos')
        table.delete_item(
            Key={
                'PK': f'VOTE#{vote_id}',
                'SK': f'USER#{user_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting vote: {str(e)}")
        return False

@handle_dynamo_error
async def get_vote_summary(target_id: str, vote_type: str) -> Dict[str, Any]:
    """Get a summary of votes for a target."""
    try:
        votes = await get_target_votes(target_id, vote_type)
        return {
            'total_votes': len(votes),
            'positive_votes': sum(1 for v in votes if v['value'] > 0),
            'negative_votes': sum(1 for v in votes if v['value'] < 0),
            'neutral_votes': sum(1 for v in votes if v['value'] == 0),
            'average_value': float(sum(v['value'] for v in votes)) / len(votes) if votes else 0
        }
    except Exception as e:
        logger.error(f"Error getting vote summary for target {target_id}: {str(e)}")
        return {} 