"""
Daily events module for Academia Tokugawa.
Handles daily announcements, subject selection, and other daily activities.
"""

import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional

from .base_events import BaseEvent
from utils.persistence.db_provider import db_provider

logger = logging.getLogger('tokugawa_bot.events.daily')

class DailyEvents(BaseEvent):
    """Handles daily events and announcements."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.daily_subject = {}
        self.player_progress = {'daily': {}}
    
    async def send_daily_announcements(self):
        """Send daily morning announcements."""
        try:
            # Get top players
            top_players = await db_provider.get_top_players(limit=5)
            
            # Create announcement message
            announcement = "**Bom dia, Academia Tokugawa!**\n\n"
            announcement += "**Top 5 Jogadores:**\n"
            
            for i, player in enumerate(top_players, 1):
                announcement += f"{i}. {player['name']} (Nível {player['level']})\n"
            
            # Send announcement
            await self.send_announcement(
                title="🌅 Anúncios Matinais",
                description=announcement,
                color=0xFFD700  # Gold
            )
            
            logger.info("Sent daily morning announcements")
            
        except Exception as e:
            logger.error(f"Error sending daily announcements: {e}")
    
    async def select_daily_subject(self):
        """Select a random subject for the day."""
        try:
            # Get subjects from database or default list
            subjects = [
                {
                    'subject': 'Matemática',
                    'emoji': '🧮',
                    'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 1
                },
                {
                    'subject': 'Português',
                    'emoji': '📚',
                    'description': 'Hoje é dia de Português! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 1
                },
                {
                    'subject': 'História',
                    'emoji': '🏛️',
                    'description': 'Hoje é dia de História! Participe do quiz para ganhar notas e XP!',
                    'difficulty': 1
                }
            ]
            
            # Select random subject
            selected = random.choice(subjects)
            self.daily_subject = selected
            
            logger.info(f"Selected daily subject: {selected['subject']}")
            
        except Exception as e:
            logger.error(f"Error selecting daily subject: {e}")
            # Set default subject
            self.daily_subject = {
                'subject': 'Matemática',
                'emoji': '🧮',
                'description': 'Hoje é dia de Matemática! Participe do quiz para ganhar notas e XP!',
                'difficulty': 1
            }
    
    async def announce_daily_subject(self):
        """Announce the daily subject."""
        try:
            if not self.daily_subject:
                await self.select_daily_subject()
            
            await self.send_announcement(
                title=f"{self.daily_subject['emoji']} {self.daily_subject['subject']}",
                description=self.daily_subject['description'],
                color=0x00FF00  # Green
            )
            
            logger.info(f"Announced daily subject: {self.daily_subject['subject']}")
            
        except Exception as e:
            logger.error(f"Error announcing daily subject: {e}")
    
    async def reset_daily_progress(self):
        """Reset daily player progress."""
        try:
            self.player_progress['daily'] = {}
            logger.info("Reset daily player progress")
        except Exception as e:
            logger.error(f"Error resetting daily progress: {e}")
    
    async def cleanup(self):
        """Clean up daily event resources."""
        try:
            self.daily_subject = {}
            self.player_progress = {'daily': {}}
            logger.info("Cleaned up daily event resources")
        except Exception as e:
            logger.error(f"Error cleaning up daily events: {e}") 