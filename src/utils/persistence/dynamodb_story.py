"""
Story operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.story')

@handle_dynamo_error
async def get_story_progress(user_id: str) -> Dict[str, Any]:
    """Get a player's story progress."""
    try:
        table = get_table('Historia')
        response = table.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROGRESS'})
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error getting story progress for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def update_story_progress(user_id: str, chapter: str, progress: Dict[str, Any]) -> bool:
    """Update a player's story progress."""
    try:
        table = get_table('Historia')
        
        # Get current progress
        current_data = await get_story_progress(user_id)
        chapters = current_data.get('chapters', {})
        
        # Update chapter progress
        chapters[chapter] = {
            **chapters.get(chapter, {}),
            **progress,
            'last_updated': datetime.now().isoformat()
        }
        
        # Store updated progress
        table.put_item(Item={
            'PK': f'PLAYER#{user_id}',
            'SK': 'PROGRESS',
            'chapters': chapters,
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error updating story progress for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_chapter_progress(user_id: str, chapter: str) -> Dict[str, Any]:
    """Get a player's progress for a specific chapter."""
    try:
        data = await get_story_progress(user_id)
        return data.get('chapters', {}).get(chapter, {})
    except Exception as e:
        logger.error(f"Error getting chapter progress for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def get_story_choices(user_id: str, chapter: str) -> List[Dict[str, Any]]:
    """Get a player's choices for a specific chapter."""
    try:
        data = await get_chapter_progress(user_id, chapter)
        return data.get('choices', [])
    except Exception as e:
        logger.error(f"Error getting story choices for player {user_id}: {str(e)}")
        return []

@handle_dynamo_error
async def record_story_choice(user_id: str, chapter: str, choice: Dict[str, Any]) -> bool:
    """Record a player's choice in a chapter."""
    try:
        current_choices = await get_story_choices(user_id, chapter)
        current_choices.append({
            **choice,
            'timestamp': datetime.now().isoformat()
        })
        
        return await update_story_progress(user_id, chapter, {'choices': current_choices})
    except Exception as e:
        logger.error(f"Error recording story choice for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_story_stats() -> Dict[str, Any]:
    """Get overall story statistics."""
    try:
        table = get_table('Historia')
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'PROGRESS'
            }
        )
        
        players = response.get('Items', [])
        if not players:
            return {}
            
        stats = {
            'total_players': len(players),
            'chapters': {},
            'choices': {}
        }
        
        for player in players:
            chapters = player.get('chapters', {})
            for chapter, data in chapters.items():
                if chapter not in stats['chapters']:
                    stats['chapters'][chapter] = 0
                stats['chapters'][chapter] += 1
                
                choices = data.get('choices', [])
                for choice in choices:
                    choice_id = choice.get('choice_id')
                    if choice_id:
                        if choice_id not in stats['choices']:
                            stats['choices'][choice_id] = 0
                        stats['choices'][choice_id] += 1
        
        return stats
    except Exception as e:
        logger.error(f"Error getting story stats: {str(e)}")
        return {} 