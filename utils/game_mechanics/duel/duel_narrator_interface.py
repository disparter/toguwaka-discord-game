"""
Interface for duel narrators in the game mechanics.
Following the Interface Segregation Principle, this provides a specific interface
for duel narration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class IDuelNarrator(ABC):
    """Interface for duel narrators."""
    
    @staticmethod
    @abstractmethod
    def generate_narration(duel_result: Dict[str, Any]) -> str:
        """Generate a narrative description of a duel.
        
        Args:
            duel_result (Dict[str, Any]): The result of the duel
            
        Returns:
            str: A narrative description of the duel
        """
        pass