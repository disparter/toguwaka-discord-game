"""
Quiz operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.quiz')

@handle_dynamo_error
async def get_quiz_question(question_id: str) -> Optional[Dict[str, Any]]:
    """Get quiz question data from database."""
    try:
        table = get_table('QuizQuestions')
        response = table.get_item(
            Key={
                'PK': f'QUIZ#{question_id}',
                'SK': 'QUESTION'
            }
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting quiz question {question_id}: {str(e)}")
        return None

@handle_dynamo_error
async def get_all_quiz_questions() -> List[Dict[str, Any]]:
    """Get all quiz questions from database."""
    try:
        table = get_table('QuizQuestions')
        response = table.scan(
            FilterExpression='begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':sk': 'QUESTION#'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all quiz questions: {str(e)}")
        return []

@handle_dynamo_error
async def get_quiz_answers(question_id: str) -> List[Dict[str, Any]]:
    """Get all answers for a quiz question from database."""
    try:
        table = get_table('QuizAnswers')
        response = table.scan(
            FilterExpression='begins_with(PK, :pk) AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': 'QUIZANSWER#',
                ':sk': f'QUESTION#{question_id}'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting quiz answers for question {question_id}: {str(e)}")
        return []

@handle_dynamo_error
async def add_quiz_question(question_id: str, question_data: Dict[str, Any]) -> bool:
    """Add a quiz question."""
    try:
        table = get_table('QuizQuestions')
        table.put_item(Item={
            'PK': f'QUIZ#{question_id}',
            'SK': 'QUESTION',
            **question_data,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error adding quiz question {question_id}: {str(e)}")
        return False

@handle_dynamo_error
async def record_quiz_answer(user_id: str, question_id: str, is_correct: bool) -> bool:
    """Record a player's answer to a quiz question."""
    try:
        table = get_table('QuizAnswers')
        table.put_item(Item={
            'PK': f'QUIZANSWER#{user_id}',
            'SK': f'QUESTION#{question_id}',
            'is_correct': is_correct,
            'timestamp': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error recording quiz answer for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_player_quiz_history(user_id: str) -> List[Dict[str, Any]]:
    """Get a player's quiz answer history."""
    try:
        table = get_table('QuizAnswers')
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'QUIZANSWER#{user_id}'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting quiz history for player {user_id}: {str(e)}")
        return []

@handle_dynamo_error
async def delete_quiz_question(question_id: str) -> bool:
    """Delete a quiz question."""
    try:
        table = get_table('QuizQuestions')
        table.delete_item(
            Key={
                'PK': f'QUIZ#{question_id}',
                'SK': 'QUESTION'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting quiz question {question_id}: {str(e)}")
        return False 