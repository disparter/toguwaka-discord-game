"""
Implementation of random events in the game mechanics.
This class is responsible for handling random events that can occur during gameplay.
"""
import random
from typing import Dict, Any, List
from utils.game_mechanics.events.event_base import EventBase
from utils.game_mechanics.constants import RANDOM_EVENTS

class RandomEvent(EventBase):
    """Class for random events."""
    
    def __init__(self, title: str, description: str, event_type: str, effect: Dict[str, Any]):
        """Initialize the random event.
        
        Args:
            title (str): The title of the event
            description (str): The description of the event
            event_type (str): The type of the event (positive, negative, neutral)
            effect (Dict[str, Any]): The effect of the event
        """
        super().__init__(title, description, event_type, effect)
    
    def trigger(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the random event for a player and return the result.
        
        Args:
            player (Dict[str, Any]): The player data
            
        Returns:
            Dict[str, Any]: The result of the event
        """
        result = {
            "title": self.get_title(),
            "description": self.get_description(),
            "type": self.get_type()
        }
        
        # Apply effects based on the event type
        effect = self.get_effect()
        
        # Experience gain/loss
        if "exp" in effect:
            result["exp_change"] = effect["exp"]
        
        # TUSD gain/loss
        if "tusd" in effect:
            result["tusd_change"] = effect["tusd"]
        
        # Attribute change
        if "attribute" in effect:
            if effect["attribute"] == "random":
                # Randomly select an attribute to improve
                attribute = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
                result["attribute_change"] = attribute
                result["attribute_value"] = 1  # Default attribute increase
            else:
                result["attribute_change"] = effect["attribute"]
                result["attribute_value"] = effect.get("attribute_value", 1)
        
        # Item reward
        if "item" in effect:
            result["item_reward"] = effect["item"]
        
        # Duel trigger
        if "duel" in effect and effect["duel"]:
            result["trigger_duel"] = True
        
        return result
    
    @staticmethod
    def create_from_template(template: Dict[str, Any]) -> 'RandomEvent':
        """Create a random event from a template.
        
        Args:
            template (Dict[str, Any]): The template for the event
            
        Returns:
            RandomEvent: A random event created from the template
        """
        return RandomEvent(
            template["title"],
            template["description"],
            template["type"],
            template["effect"]
        )
    
    @staticmethod
    def get_random_event() -> Dict[str, Any]:
        """Get a random event template.
        
        Returns:
            Dict[str, Any]: A random event template
        """
        return random.choice(RANDOM_EVENTS)
    
    @staticmethod
    def create_random_event() -> 'RandomEvent':
        """Create a random event.
        
        Returns:
            RandomEvent: A randomly generated event
        """
        template = RandomEvent.get_random_event()
        return RandomEvent.create_from_template(template)