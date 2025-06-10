"""
Implementation of story events in the game mechanics.
This class is responsible for handling events that occur during the story mode.
"""
import random
from typing import Dict, Any, List, Optional
from utils.game_mechanics.events.event_base import EventBase

class StoryEvent(EventBase):
    """Class for story events."""
    
    def __init__(self, title: str, description: str, chapter_id: str, event_type: str = "story", 
                 rewards: Dict[str, Any] = None, choices: List[Dict[str, Any]] = None):
        """Initialize the story event.
        
        Args:
            title (str): The title of the event
            description (str): The description of the event
            chapter_id (str): The ID of the chapter this event belongs to
            event_type (str, optional): The type of the event. Defaults to "story".
            rewards (Dict[str, Any], optional): The rewards for completing the event. Defaults to None.
            choices (List[Dict[str, Any]], optional): The choices available for this event. Defaults to None.
        """
        effect = {
            "chapter_id": chapter_id,
            "rewards": rewards or {},
            "choices": choices or []
        }
        
        super().__init__(title, description, event_type, effect)
    
    def trigger(self, player: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger the story event for a player and return the result.
        
        Args:
            player (Dict[str, Any]): The player data
            
        Returns:
            Dict[str, Any]: The result of the event, including rewards and choices
        """
        result = {
            "title": self.get_title(),
            "description": self.get_description(),
            "type": self.get_type(),
            "chapter_id": self.get_effect().get("chapter_id", ""),
            "choices": self.get_effect().get("choices", [])
        }
        
        # Apply rewards if there are no choices or if this is a completion event
        if not result["choices"] or self.get_type() == "story_completion":
            rewards = self.get_effect().get("rewards", {})
            
            # Experience reward
            if "exp" in rewards:
                result["exp_change"] = rewards["exp"]
            
            # TUSD reward
            if "tusd" in rewards:
                result["tusd_change"] = rewards["tusd"]
            
            # Attribute reward
            if "attribute" in rewards:
                result["attribute_change"] = rewards["attribute"]
                result["attribute_value"] = rewards.get("attribute_value", 1)
            
            # Item reward
            if "item" in rewards:
                result["item_reward"] = rewards["item"]
            
            # Special rewards
            if "special" in rewards:
                result["special_reward"] = rewards["special"]
            
            # Story progress
            if "progress" in rewards:
                result["story_progress"] = rewards["progress"]
        
        return result
    
    def process_choice(self, player: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """Process a player's choice for this event.
        
        Args:
            player (Dict[str, Any]): The player data
            choice_index (int): The index of the chosen option
            
        Returns:
            Dict[str, Any]: The result of the choice
        """
        choices = self.get_effect().get("choices", [])
        
        if not choices or choice_index >= len(choices):
            return {"error": "Invalid choice"}
        
        choice = choices[choice_index]
        
        result = {
            "title": self.get_title(),
            "description": choice.get("description", ""),
            "type": self.get_type(),
            "chapter_id": self.get_effect().get("chapter_id", ""),
            "choice_index": choice_index
        }
        
        # Apply rewards for this choice
        rewards = choice.get("rewards", {})
        
        # Experience reward
        if "exp" in rewards:
            result["exp_change"] = rewards["exp"]
        
        # TUSD reward
        if "tusd" in rewards:
            result["tusd_change"] = rewards["tusd"]
        
        # Attribute reward
        if "attribute" in rewards:
            result["attribute_change"] = rewards["attribute"]
            result["attribute_value"] = rewards.get("attribute_value", 1)
        
        # Item reward
        if "item" in rewards:
            result["item_reward"] = rewards["item"]
        
        # Special rewards
        if "special" in rewards:
            result["special_reward"] = rewards["special"]
        
        # Story progress
        if "progress" in rewards:
            result["story_progress"] = rewards["progress"]
        
        # Next event
        if "next_event" in choice:
            result["next_event"] = choice["next_event"]
        
        return result
    
    @staticmethod
    def create_from_json(event_data: Dict[str, Any]) -> Optional['StoryEvent']:
        """Create a story event from JSON data.
        
        Args:
            event_data (Dict[str, Any]): The event data from a JSON file
            
        Returns:
            Optional[StoryEvent]: A story event created from the data, or None if the data is invalid
        """
        if not event_data:
            return None
        
        title = event_data.get("title", "")
        description = event_data.get("description", "")
        chapter_id = event_data.get("chapter_id", "")
        event_type = event_data.get("type", "story")
        rewards = event_data.get("rewards", {})
        choices = event_data.get("choices", [])
        
        return StoryEvent(title, description, chapter_id, event_type, rewards, choices)