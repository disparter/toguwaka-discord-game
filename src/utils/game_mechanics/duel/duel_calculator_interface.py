"""
Interface for duel calculators in the game mechanics.
Following the Interface Segregation Principle, this provides a specific interface
for duel-related calculations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class IDuelCalculator(ABC):
    """Interface for duel calculators."""
    
    @staticmethod
    @abstractmethod
    def calculate_outcome(challenger: Dict[str, Any], opponent: Dict[str, Any], duel_type: str) -> Dict[str, Any]:
        """Calculate the outcome of a duel between two players.
        
        Args:
            challenger (Dict[str, Any]): The challenger's data
            opponent (Dict[str, Any]): The opponent's data
            duel_type (str): The type of duel (physical, mental, strategic, social)
            
        Returns:
            Dict[str, Any]: The result of the duel
        """
        pass