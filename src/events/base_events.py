"""
Base module for event handling in Academia Tokugawa.
This module provides common functionality and base classes for all events.
"""

import logging
import discord
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger('tokugawa_bot.events')

class BaseEvent:
    """Base class for all events."""
    
    def __init__(self, bot, channel_id: Optional[int] = None):
        self.bot = bot
        self.channel_id = channel_id
        self.event_data: Dict[str, Any] = {}
    
    async def find_channel(self, channel_names: List[str]) -> Optional[discord.TextChannel]:
        """Find a channel by name in any guild."""
        for guild in self.bot.guilds:
            for channel_name in channel_names:
                channel = discord.utils.get(guild.text_channels, name=channel_name)
                if channel:
                    return channel
        return None
    
    async def send_announcement(self, title: str, description: str, color: int = 0x00FF00) -> Optional[discord.Message]:
        """Send an announcement to the event channel."""
        if not self.channel_id:
            logger.error("No channel ID set for event announcement")
            return None
            
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            logger.error(f"Could not find channel with ID {self.channel_id}")
            return None
            
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        try:
            return await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending announcement: {e}")
            return None
    
    def create_basic_embed(self, title: str, description: str, color: int = 0x00FF00) -> discord.Embed:
        """Create a basic embed for announcements."""
        return discord.Embed(
            title=title,
            description=description,
            color=color
        )
    
    async def cleanup(self):
        """Clean up event resources."""
        pass 