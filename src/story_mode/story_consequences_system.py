"""
Consequences System for the story mode.

This module provides a high-level interface for managing consequences
of player choices and actions in the story mode.
"""

import logging
from typing import Dict, Any, Optional, List
from .story_consequences import Consequences

logger = logging.getLogger('tokugawa_bot')

class ConsequencesSystem:
    """
    System for managing consequences of player choices and actions.
    This class serves as a high-level interface to the Consequences class.
    """
    
    def __init__(self):
        """Initialize the consequences system."""
        self.consequences = Consequences()
        logger.info("ConsequencesSystem initialized")

    def apply_consequences(self, player_data: Dict[str, Any], choice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply consequences for a player's choice.
        
        Args:
            player_data: The player's current data
            choice_data: The choice data containing consequences
            
        Returns:
            Updated player data with consequences applied
        """
        try:
            return self.consequences.apply_consequences(player_data, choice_data)
        except Exception as e:
            logger.error(f"Error applying consequences: {e}")
            return player_data

    def get_available_consequences(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get available consequences for the player's current state.
        
        Args:
            player_data: The player's current data
            
        Returns:
            List of available consequences
        """
        try:
            return self.consequences.get_available_consequences(player_data)
        except Exception as e:
            logger.error(f"Error getting available consequences: {e}")
            return []

    def validate_consequences(self, consequences_data: Dict[str, Any]) -> bool:
        """
        Validate if the consequences data is valid.
        
        Args:
            consequences_data: The consequences data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            return self.consequences.validate_consequences(consequences_data)
        except Exception as e:
            logger.error(f"Error validating consequences: {e}")
            return False 