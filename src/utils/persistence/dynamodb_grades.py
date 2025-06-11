"""
Grade operations for DynamoDB.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
from utils.logging_config import get_logger
from utils.persistence.dynamodb import handle_dynamo_error, get_table

logger = get_logger('tokugawa_bot.grades')

@handle_dynamo_error
async def get_player_grades(user_id: str) -> Dict[str, Dict[str, float]]:
    """Get all grades for a player."""
    try:
        table = get_table('Notas')
        response = table.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'GRADES'})
        return response.get('Item', {}).get('grades', {})
    except Exception as e:
        logger.error(f"Error getting grades for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def update_player_grade(user_id: str, subject: str, grade: float) -> bool:
    """Update a player's grade for a subject."""
    try:
        # Get current grades
        grades = await get_player_grades(user_id)

        # Update grade - convert float to Decimal for DynamoDB compatibility
        if subject not in grades:
            grades[subject] = {}
        grades[subject][datetime.now().strftime('%Y-%m')] = Decimal(str(grade))

        # Store updated grades
        table = get_table('Notas')
        table.put_item(Item={
            'PK': f'PLAYER#{user_id}',
            'SK': 'GRADES',
            'grades': grades,
            'last_updated': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        logger.error(f"Error updating grade for player {user_id}: {str(e)}")
        return False

@handle_dynamo_error
async def get_monthly_average_grades(user_id: str) -> Dict[str, float]:
    """Get monthly average grades for a player."""
    try:
        grades = await get_player_grades(user_id)
        averages = {}

        for subject, monthly_grades in grades.items():
            if monthly_grades:
                total = sum(monthly_grades.values())
                count = len(monthly_grades)
                averages[subject] = float(total) / count

        return averages
    except Exception as e:
        logger.error(f"Error calculating monthly averages for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def get_subject_grades(user_id: str, subject: str) -> Dict[str, float]:
    """Get all grades for a specific subject."""
    try:
        grades = await get_player_grades(user_id)
        return grades.get(subject, {})
    except Exception as e:
        logger.error(f"Error getting subject grades for player {user_id}: {str(e)}")
        return {}

@handle_dynamo_error
async def get_all_students_grades() -> List[Dict[str, Any]]:
    """Get grades for all students."""
    try:
        table = get_table('Notas')
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'GRADES'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all students grades: {str(e)}")
        return []

@handle_dynamo_error
async def get_top_students_by_subject(subject: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top students by subject."""
    try:
        all_grades = await get_all_students_grades()
        subject_grades = []

        for student in all_grades:
            grades = student.get('grades', {}).get(subject, {})
            if grades:
                avg = sum(grades.values()) / len(grades)
                subject_grades.append({
                    'user_id': student['PK'].replace('PLAYER#', ''),
                    'average': float(avg),
                    'grades': grades
                })

        return sorted(subject_grades, key=lambda x: x['average'], reverse=True)[:limit]
    except Exception as e:
        logger.error(f"Error getting top students for subject {subject}: {str(e)}")
        return [] 