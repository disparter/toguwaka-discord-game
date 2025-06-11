"""
Special events module for Academia Tokugawa.
Handles special events like holidays, seasonal events, and other unique activities.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .base_events import BaseEvent
from utils.persistence.db_provider import db_provider

logger = logging.getLogger('tokugawa_bot.events.special')

class SpecialEvents(BaseEvent):
    """Handles special events and seasonal activities."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.current_event = None
        self.event_participants = []
        self.event_start_time = None
        self.event_end_time = None
    
    async def check_for_special_events(self):
        """Check if there are any special events that should start."""
        try:
            current_date = datetime.now()
            
            # Check for holidays and special dates
            special_dates = {
                (1, 1): {
                    'name': 'Ano Novo',
                    'emoji': '🎆',
                    'description': 'Celebre o Ano Novo com a Academia Tokugawa!',
                    'duration': 48,  # hours
                    'prize': 2000
                },
                (12, 25): {
                    'name': 'Natal',
                    'emoji': '🎄',
                    'description': 'Feliz Natal da Academia Tokugawa!',
                    'duration': 48,
                    'prize': 2000
                }
            }
            
            # Check if current date matches any special date
            current_month_day = (current_date.month, current_date.day)
            if current_month_day in special_dates:
                await self.start_special_event(special_dates[current_month_day])
            
        except Exception as e:
            logger.error(f"Error checking for special events: {e}")
    
    async def start_special_event(self, event_data: Dict[str, Any]):
        """Start a new special event."""
        try:
            self.current_event = event_data
            self.event_start_time = datetime.now()
            self.event_end_time = self.event_start_time + timedelta(hours=event_data['duration'])
            
            # Announce event
            await self.send_announcement(
                title=f"{event_data['emoji']} {event_data['name']}",
                description=f"{event_data['description']}\n\n"
                           f"Prêmio: {event_data['prize']} pontos\n"
                           f"Duração: {event_data['duration']} horas\n\n"
                           f"Use `/evento participar` para participar!",
                color=0x800080  # Purple
            )
            
            logger.info(f"Started special event: {event_data['name']}")
            
        except Exception as e:
            logger.error(f"Error starting special event: {e}")
    
    async def add_event_participant(self, user_id: int, username: str) -> bool:
        """Add a participant to the current special event."""
        try:
            if not self.current_event:
                return False
            
            if datetime.now() > self.event_end_time:
                return False
            
            # Check if user is already participating
            if any(p['user_id'] == user_id for p in self.event_participants):
                return False
            
            # Add participant
            self.event_participants.append({
                'user_id': user_id,
                'username': username,
                'joined_at': datetime.now()
            })
            
            logger.info(f"Added special event participant: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding special event participant: {e}")
            return False
    
    async def end_special_event(self):
        """End the current special event and award prizes."""
        try:
            if not self.current_event:
                return
            
            # Award prizes to all participants
            for participant in self.event_participants:
                await db_provider.add_points(
                    participant['user_id'],
                    self.current_event['prize']
                )
            
            # Create results message
            results = f"**Resultados do {self.current_event['name']}**\n\n"
            results += f"Total de participantes: {len(self.event_participants)}\n"
            results += f"Prêmio por participante: {self.current_event['prize']} pontos\n\n"
            results += "**Participantes:**\n"
            
            for participant in self.event_participants:
                results += f"• {participant['username']}\n"
            
            # Announce results
            await self.send_announcement(
                title=f"🎉 {self.current_event['name']} - Resultados",
                description=results,
                color=0x800080  # Purple
            )
            
            # Reset event
            self.current_event = None
            self.event_participants = []
            self.event_start_time = None
            self.event_end_time = None
            
            logger.info("Ended special event")
            
        except Exception as e:
            logger.error(f"Error ending special event: {e}")
    
    async def cleanup(self):
        """Clean up special event resources."""
        try:
            self.current_event = None
            self.event_participants = []
            self.event_start_time = None
            self.event_end_time = None
            logger.info("Cleaned up special event resources")
        except Exception as e:
            logger.error(f"Error cleaning up special events: {e}") 