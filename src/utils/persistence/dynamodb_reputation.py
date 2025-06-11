"""
Reputation operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.reputation')

@handle_dynamo_error
async def update_player_reputation(user_id: str, amount: int, reason: str) -> bool:
    """Update a player's reputation."""
    try:
        table = get_table('Reputacao')
        
        # Get current reputation
        response = table.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'REPUTATION'})
        current_data = response.get('Item', {})
        
        # Calculate new reputation
        current_rep = current_data.get('reputation', Decimal('0'))
        new_rep = current_rep + Decimal(str(amount))
        
        # Update reputation
        table.put_item(Item={
            'PK': f'PLAYER#{user_id}',
            'SK': 'REPUTATION',
            'reputation': new_rep,
            'last_updated': datetime.now().isoformat(),
            'history': current_data.get('history', []) + [{
                'amount': Decimal(str(amount)),
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }]
        })
        return True
    except Exception as e:
        logger.error(f"Error updating reputation for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_player_reputation(user_id: str) -> Dict[str, Any]:
    """Get a player's reputation data."""
    try:
        table = get_table('Reputacao')
        response = table.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'REPUTATION'})
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error getting reputation for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def get_top_players_by_reputation(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top players by reputation."""
    try:
        table = get_table('Reputacao')
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'REPUTATION'
            }
        )
        
        players = response.get('Items', [])
        sorted_players = sorted(players, key=lambda x: x.get('reputation', 0), reverse=True)
        return sorted_players[:limit]
    except Exception as e:
        logger.error(f"Error getting top players by reputation: {str(e)}")
        return []

@handle_dynamo_error
async def get_reputation_history(user_id: str) -> List[Dict[str, Any]]:
    """Get a player's reputation history."""
    try:
        data = await get_player_reputation(user_id)
        return data.get('history', [])
    except Exception as e:
        logger.error(f"Error getting reputation history for player {user_id}: {str(e)}")
        return []

@handle_dynamo_error
async def get_reputation_rank(user_id: str) -> int:
    """Get a player's reputation rank."""
    try:
        all_players = await get_top_players_by_reputation(limit=1000)  # Get all players
        for i, player in enumerate(all_players, 1):
            if player['PK'] == f'PLAYER#{user_id}':
                return i
        return len(all_players) + 1  # If not found, return last rank
    except Exception as e:
        logger.error(f"Error getting reputation rank for player {user_id}: {str(e)}")
        return 0

@handle_dynamo_error
async def get_reputation_stats() -> Dict[str, Any]:
    """Get overall reputation statistics."""
    try:
        all_players = await get_top_players_by_reputation(limit=1000)
        if not all_players:
            return {}
            
        reputations = [float(p.get('reputation', 0)) for p in all_players]
        return {
            'total_players': len(all_players),
            'average_reputation': sum(reputations) / len(reputations),
            'highest_reputation': max(reputations),
            'lowest_reputation': min(reputations),
            'median_reputation': sorted(reputations)[len(reputations) // 2]
        }
    except Exception as e:
        logger.error(f"Error getting reputation stats: {str(e)}")
        return {} 