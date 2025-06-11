"""
Events manager module for Academia Tokugawa.
Coordinates and manages all types of events (daily, weekly, special).
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .daily_events import DailyEvents
from .weekly_events import WeeklyEvents
from .special_events import SpecialEvents

logger = logging.getLogger('tokugawa_bot.events.manager')

class EventsManager:
    """Manages and coordinates all types of events."""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_events = DailyEvents(bot)
        self.weekly_events = WeeklyEvents(bot)
        self.special_events = SpecialEvents(bot)
        self.is_running = False
        self.task = None
    
    async def start(self):
        """Start the events manager."""
        try:
            if self.is_running:
                return
            
            self.is_running = True
            self.task = asyncio.create_task(self._run_event_loop())
            logger.info("Started events manager")
            
        except Exception as e:
            logger.error(f"Error starting events manager: {e}")
            self.is_running = False
    
    async def stop(self):
        """Stop the events manager."""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            
            # Clean up all events
            await self.daily_events.cleanup()
            await self.weekly_events.cleanup()
            await self.special_events.cleanup()
            
            logger.info("Stopped events manager")
            
        except Exception as e:
            logger.error(f"Error stopping events manager: {e}")
    
    async def _run_event_loop(self):
        """Main event loop that manages all events."""
        try:
            while self.is_running:
                current_time = datetime.now()
                
                # Check for special events
                await self.special_events.check_for_special_events()
                
                # Handle daily events
                if current_time.hour == 0 and current_time.minute == 0:
                    await self.daily_events.send_daily_announcements()
                    await self.daily_events.select_daily_subject()
                    await self.daily_events.announce_daily_subject()
                    await self.daily_events.reset_daily_progress()
                
                # Handle weekly events
                if current_time.weekday() == 0 and current_time.hour == 0 and current_time.minute == 0:
                    await self.weekly_events.start_weekly_tournament()
                
                # Check for ending events
                if self.weekly_events.current_tournament and current_time > self.weekly_events.tournament_end_time:
                    await self.weekly_events.end_tournament()
                
                if self.special_events.current_event and current_time > self.special_events.event_end_time:
                    await self.special_events.end_special_event()
                
                # Wait for next minute
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info("Event loop cancelled")
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
            self.is_running = False
    
    async def get_current_events(self) -> Dict[str, Any]:
        """Get information about current events."""
        try:
            events = {
                'daily': {
                    'subject': self.daily_events.daily_subject
                },
                'weekly': {
                    'tournament': self.weekly_events.current_tournament,
                    'participants': len(self.weekly_events.tournament_participants),
                    'end_time': self.weekly_events.tournament_end_time
                },
                'special': {
                    'event': self.special_events.current_event,
                    'participants': len(self.special_events.event_participants),
                    'end_time': self.special_events.event_end_time
                }
            }
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting current events: {e}")
            return {} 