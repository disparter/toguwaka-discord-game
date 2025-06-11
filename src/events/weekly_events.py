"""
Weekly events module for Academia Tokugawa.
Handles weekly tournaments, competitions, and other weekly activities.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .base_events import BaseEvent
from utils.persistence.db_provider import db_provider

logger = logging.getLogger('tokugawa_bot.events.weekly')

class WeeklyEvents(BaseEvent):
    """Handles weekly events and tournaments."""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.current_tournament = None
        self.tournament_participants = []
        self.tournament_start_time = None
        self.tournament_end_time = None
    
    async def start_weekly_tournament(self):
        """Start a new weekly tournament."""
        try:
            # Get tournament type
            tournament_types = [
                {
                    'name': 'Torneio de Matemática',
                    'emoji': '🧮',
                    'description': 'Um torneio de matemática para testar suas habilidades!',
                    'prize': 1000,
                    'duration': 24  # hours
                },
                {
                    'name': 'Torneio de Português',
                    'emoji': '📚',
                    'description': 'Um torneio de português para testar suas habilidades!',
                    'prize': 1000,
                    'duration': 24
                },
                {
                    'name': 'Torneio de História',
                    'emoji': '🏛️',
                    'description': 'Um torneio de história para testar suas habilidades!',
                    'prize': 1000,
                    'duration': 24
                }
            ]
            
            # Select random tournament type
            self.current_tournament = random.choice(tournament_types)
            self.tournament_start_time = datetime.now()
            self.tournament_end_time = self.tournament_start_time + timedelta(hours=self.current_tournament['duration'])
            
            # Announce tournament
            await self.send_announcement(
                title=f"{self.current_tournament['emoji']} {self.current_tournament['name']}",
                description=f"{self.current_tournament['description']}\n\n"
                           f"Prêmio: {self.current_tournament['prize']} pontos\n"
                           f"Duração: {self.current_tournament['duration']} horas\n\n"
                           f"Use `/torneio participar` para participar!",
                color=0xFF0000  # Red
            )
            
            logger.info(f"Started weekly tournament: {self.current_tournament['name']}")
            
        except Exception as e:
            logger.error(f"Error starting weekly tournament: {e}")
    
    async def add_tournament_participant(self, user_id: int, username: str) -> bool:
        """Add a participant to the current tournament."""
        try:
            if not self.current_tournament:
                return False
            
            if datetime.now() > self.tournament_end_time:
                return False
            
            # Check if user is already participating
            if any(p['user_id'] == user_id for p in self.tournament_participants):
                return False
            
            # Add participant
            self.tournament_participants.append({
                'user_id': user_id,
                'username': username,
                'score': 0,
                'joined_at': datetime.now()
            })
            
            logger.info(f"Added tournament participant: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding tournament participant: {e}")
            return False
    
    async def update_tournament_score(self, user_id: int, score: int) -> bool:
        """Update a participant's tournament score."""
        try:
            if not self.current_tournament:
                return False
            
            # Find participant
            participant = next((p for p in self.tournament_participants if p['user_id'] == user_id), None)
            if not participant:
                return False
            
            # Update score
            participant['score'] = score
            logger.info(f"Updated tournament score for {participant['username']}: {score}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tournament score: {e}")
            return False
    
    async def end_tournament(self):
        """End the current tournament and announce results."""
        try:
            if not self.current_tournament:
                return
            
            # Sort participants by score
            sorted_participants = sorted(
                self.tournament_participants,
                key=lambda x: x['score'],
                reverse=True
            )
            
            # Create results message
            results = f"**Resultados do {self.current_tournament['name']}**\n\n"
            
            for i, participant in enumerate(sorted_participants[:3], 1):
                results += f"{i}. {participant['username']} - {participant['score']} pontos\n"
            
            # Award prizes
            for i, participant in enumerate(sorted_participants[:3], 1):
                prize = self.current_tournament['prize'] // (2 ** (i - 1))
                await db_provider.add_points(participant['user_id'], prize)
            
            # Announce results
            await self.send_announcement(
                title=f"🏆 {self.current_tournament['name']} - Resultados",
                description=results,
                color=0xFFD700  # Gold
            )
            
            # Reset tournament
            self.current_tournament = None
            self.tournament_participants = []
            self.tournament_start_time = None
            self.tournament_end_time = None
            
            logger.info("Ended weekly tournament")
            
        except Exception as e:
            logger.error(f"Error ending tournament: {e}")
    
    async def cleanup(self):
        """Clean up weekly event resources."""
        try:
            self.current_tournament = None
            self.tournament_participants = []
            self.tournament_start_time = None
            self.tournament_end_time = None
            logger.info("Cleaned up weekly event resources")
        except Exception as e:
            logger.error(f"Error cleaning up weekly events: {e}") 