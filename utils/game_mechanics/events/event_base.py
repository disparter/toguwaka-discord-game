"""
Abstract base class for events in the game mechanics.
This class implements common functionality for all events.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from utils.game_mechanics.events.event_interface import IEvent

class EventBase(IEvent, ABC):
    """Abstract base class for all events."""
    
    def __init__(self, title: str, description: str, event_type: str, effect: Dict[str, Any]):
        """Initialize the event with basic information.
        
        Args:
            title (str): The title of the event
            description (str): The description of the event
            event_type (str): The type of the event (positive, negative, neutral)
            effect (Dict[str, Any]): The effect of the event
        """
        self._title = title
        self._description = description
        self._type = event_type
        self._effect = effect
    
    def get_title(self) -> str:
        """Get the title of the event."""
        return self._title
    
    def get_description(self) -> str:
        """Get the description of the event."""
        return self._description
    
    def get_type(self) -> str:
        """Get the type of the event (positive, negative, neutral)."""
        return self._type
    
    def get_effect(self) -> Dict[str, Any]:
        """Get the effect of the event."""
        return self._effect
    
    @abstractmethod
    def trigger(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the event for a player and return the result.
        
        This method must be implemented by concrete event classes.
        
        Args:
            player (Dict[str, Any]): The player data
            
        Returns:
            Dict[str, Any]: The result of the event
        """
        pass