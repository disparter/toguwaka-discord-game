"""
Implementation of training events in the game mechanics.
This class is responsible for handling training events.
"""
import random
from typing import Dict, Any, List
from utils.game_mechanics.events.event_base import EventBase
from utils.game_mechanics.constants import TRAINING_OUTCOMES

class TrainingEvent(EventBase):
    """Class for training events."""
    
    def __init__(self, title: str, description: str, exp_gain: int, attribute_gain: str = None):
        """Initialize the training event.
        
        Args:
            title (str): The title of the event
            description (str): The description of the event
            exp_gain (int): The amount of experience gained from the event
            attribute_gain (str, optional): The attribute that will be increased. Defaults to None.
        """
        effect = {"exp": exp_gain}
        if attribute_gain:
            effect["attribute"] = attribute_gain
        
        super().__init__(title, description, "training", effect)
    
    def trigger(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the training event for a player and return the result.
        
        Args:
            player (Dict[str, Any]): The player data
            
        Returns:
            Dict[str, Any]: The result of the event, including experience and attribute gains
        """
        result = {
            "title": self.get_title(),
            "description": self.get_description(),
            "exp_gain": self.get_effect().get("exp", 0)
        }
        
        # Apply attribute gain if specified
        if "attribute" in self.get_effect():
            attribute = self.get_effect()["attribute"]
            result["attribute_gain"] = attribute
            result["attribute_value"] = 1  # Default attribute increase
        
        return result
    
    @staticmethod
    def create_random_training_event() -> 'TrainingEvent':
        """Create a random training event.
        
        Returns:
            TrainingEvent: A randomly generated training event
        """
        # Get a random training outcome for the description
        description = random.choice(TRAINING_OUTCOMES)
        
        # Generate random experience gain (10-30)
        exp_gain = random.randint(10, 30)
        
        # Randomly select an attribute to improve
        attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
        
        return TrainingEvent("Treinamento Concluído", description, exp_gain, attribute)
    
    @staticmethod
    def get_random_outcome() -> str:
        """Get a random training outcome message.
        
        Returns:
            str: A random training outcome message
        """
        return random.choice(TRAINING_OUTCOMES)