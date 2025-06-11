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
        table = get_table('AcademiaTokugawa')
        response = await table.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'STORY_PROGRESS'})
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error getting story progress for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def update_story_progress(user_id: str, progress_data: Dict[str, Any]) -> bool:
    """Update a player's story progress."""
    try:
        table = get_table('AcademiaTokugawa')
        
        # Get current progress
        current_data = await get_story_progress(user_id)
        
        # Update progress
        updated_data = {
            'PK': f'PLAYER#{user_id}',
            'SK': 'STORY_PROGRESS',
            **current_data,
            **progress_data,
            'last_updated': datetime.now().isoformat()
        }
        
        # Store updated progress
        await table.put_item(Item=updated_data)
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
        
        return await update_story_progress(user_id, {'choices': current_choices})
    except Exception as e:
        logger.error(f"Error recording story choice for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_story_stats() -> Dict[str, Any]:
    """Get overall story statistics."""
    try:
        table = get_table('AcademiaTokugawa')
        response = await table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'STORY_PROGRESS'
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
            chapters = player.get('completed_chapters', [])
            for chapter in chapters:
                if chapter not in stats['chapters']:
                    stats['chapters'][chapter] = 0
                stats['chapters'][chapter] += 1
                
            choices = player.get('story_choices', {})
            for chapter_id, chapter_choices in choices.items():
                for choice_key, choice_value in chapter_choices.items():
                    choice_id = f"{chapter_id}:{choice_key}"
                    if choice_id not in stats['choices']:
                        stats['choices'][choice_id] = 0
                    stats['choices'][choice_id] += 1
        
        return stats
    except Exception as e:
        logger.error(f"Error getting story stats: {str(e)}")
        return {} 