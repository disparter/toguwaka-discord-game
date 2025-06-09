"""
Interface for events in the game mechanics.
Following the Interface Segregation Principle, this provides a base interface
that specific event types will extend.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class IEvent(ABC):
    """Base interface for all events."""
    
    @abstractmethod
    def get_title(self) -> str:
        """Get the title of the event."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get the description of the event."""
        pass
    
    @abstractmethod
    def get_type(self) -> str:
        """Get the type of the event (positive, negative, neutral)."""
        pass
    
    @abstractmethod
    def get_effect(self) -> Dict[str, Any]:
        """Get the effect of the event."""
        pass
    
    @abstractmethod
    def trigger(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the event for a player and return the result."""
        pass