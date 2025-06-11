"""
Scheduled tasks for the bot.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from utils.logging_config import get_logger
from utils.persistence.dynamodb_item_usage import clear_expired_usage_records
from utils.persistence.dynamodb_cooldowns import clear_expired_cooldowns

logger = get_logger('tokugawa_bot.scheduled_tasks')

async def cleanup_expired_records():
    """Clean up expired records from various tables."""
    try:
        # Clear expired cooldowns
        cooldowns_cleared = await clear_expired_cooldowns()
        logger.info(f"Cleared {cooldowns_cleared} expired cooldowns")
        
        # Clear expired item usage records
        usage_records_cleared = await clear_expired_usage_records()
        logger.info(f"Cleared {usage_records_cleared} expired item usage records")
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")

async def run_scheduled_tasks():
    """Run all scheduled tasks."""
    while True:
        try:
            await cleanup_expired_records()
            # Wait for 1 hour before next cleanup
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in scheduled tasks: {str(e)}")
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300) 