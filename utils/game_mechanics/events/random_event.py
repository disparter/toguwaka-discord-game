"""
Implementation of random events in the game mechanics.
This class is responsible for handling random events that can occur during gameplay.
"""
import random
import logging
import json
import os
from typing import Dict, Any, List, Optional
from utils.game_mechanics.events.event_base import EventBase
from utils.game_mechanics.constants import RANDOM_EVENTS

# Get logger
logger = logging.getLogger('tokugawa_bot')

# Function to load events from JSON files
def load_events_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load events from a JSON file.

    Args:
        file_path (str): Path to the JSON file

    Returns:
        List[Dict[str, Any]]: List of event dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        logger.info(f"Successfully loaded {len(events)} events from {file_path}")
        return events
    except FileNotFoundError:
        logger.warning(f"Events file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading events from {file_path}: {e}")
        return []

# Load extended random events from JSON file
EXTENDED_RANDOM_EVENTS_PATH = os.path.join('data', 'events', 'extended_random_events.json')
EXTENDED_RANDOM_EVENTS = load_events_from_json(EXTENDED_RANDOM_EVENTS_PATH)

# If extended events couldn't be loaded, use hardcoded fallback
if not EXTENDED_RANDOM_EVENTS:
    logger.warning("Using fallback hardcoded extended random events")
    # Fallback to original RANDOM_EVENTS with added category and rarity
    EXTENDED_RANDOM_EVENTS = []
    for event in RANDOM_EVENTS:
        extended_event = event.copy()
        # Add default category and rarity if not present
        if "category" not in extended_event:
            extended_event["category"] = "general"
        if "rarity" not in extended_event:
            extended_event["rarity"] = "common"
        EXTENDED_RANDOM_EVENTS.append(extended_event)

class RandomEvent(EventBase):
    """Class for random events."""

    # Track last events to avoid repetition
    _last_events = []
    _max_history = 3  # Don't repeat the last 3 events

    def __init__(self, title: str, description: str, event_type: str, effect: Dict[str, Any], 
                 category: str = "general", rarity: str = "common"):
        """Initialize the random event.

        Args:
            title (str): The title of the event
            description (str): The description of the event
            event_type (str): The type of the event (positive, negative, neutral)
            effect (Dict[str, Any]): The effect of the event
            category (str): The category of the event
            rarity (str): The rarity of the event
        """
        super().__init__(title, description, event_type, effect)
        self.category = category
        self.rarity = rarity

    def get_category(self) -> str:
        """Get the category of the event."""
        return self.category

    def get_rarity(self) -> str:
        """Get the rarity of the event."""
        return self.rarity

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
            "type": self.get_type(),
            "category": self.get_category(),
            "rarity": self.get_rarity()
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

        # Direct attribute changes
        for attr in ["dexterity", "intellect", "charisma", "power_stat"]:
            if attr in effect:
                result["attribute_change"] = attr
                result["attribute_value"] = effect[attr]

        # All attributes boost
        if "all_attributes" in effect:
            value = effect["all_attributes"]
            result["all_attributes_change"] = value
            # Choose a primary attribute to display in the embed
            result["attribute_change"] = random.choice(["dexterity", "intellect", "charisma", "power_stat"])
            result["attribute_value"] = value

        # Random attribute changes (positive and negative)
        if "random_attribute_change" in effect and effect["random_attribute_change"]:
            attributes = ["dexterity", "intellect", "charisma", "power_stat"]
            # Randomly increase one attribute and decrease another
            increase_attr = random.choice(attributes)
            attributes.remove(increase_attr)
            decrease_attr = random.choice(attributes)

            result["attribute_change"] = increase_attr
            result["attribute_value"] = 1
            result["secondary_attribute_change"] = decrease_attr
            result["secondary_attribute_value"] = -1

        # Random negative effect
        if "random_negative" in effect and effect["random_negative"]:
            negative_effects = [
                {"tusd": -30},
                {"dexterity": -1},
                {"intellect": -1},
                {"charisma": -1}
            ]
            negative_effect = random.choice(negative_effects)
            for key, value in negative_effect.items():
                if key == "tusd":
                    result["tusd_change"] = value
                else:
                    result["secondary_attribute_change"] = key
                    result["secondary_attribute_value"] = value

        # Item reward
        if "item" in effect:
            if effect["item"] == "random":
                rarities = ["common", "uncommon", "rare", "epic", "legendary"]
                weights = [50, 30, 15, 4, 1]  # Probability weights
                item_rarity = random.choices(rarities, weights=weights, k=1)[0]
                result["item_reward"] = f"Item {item_rarity.capitalize()}"
                result["item_rarity"] = item_rarity
            else:
                result["item_reward"] = f"Item {effect['item'].capitalize()}"
                result["item_rarity"] = effect["item"]

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
            template["effect"],
            template.get("category", "general"),
            template.get("rarity", "common")
        )

    @staticmethod
    def get_random_event() -> Dict[str, Any]:
        """Get a random event template, avoiding recent events.

        Returns:
            Dict[str, Any]: A random event template
        """
        # Use extended events if available, otherwise fall back to original events
        events_pool = EXTENDED_RANDOM_EVENTS if EXTENDED_RANDOM_EVENTS else RANDOM_EVENTS

        # Filter out recently used events to avoid repetition
        available_events = [e for e in events_pool if e["title"] not in RandomEvent._last_events]

        # If we've filtered out all events, reset history
        if not available_events:
            RandomEvent._last_events = []
            available_events = events_pool

        # Apply rarity weights for selection
        rarities = {
            "common": 50,
            "uncommon": 30,
            "rare": 15,
            "epic": 4,
            "legendary": 1
        }

        # Calculate weights based on rarity
        weights = [rarities.get(e.get("rarity", "common"), 50) for e in available_events]

        # Select an event based on weights
        selected_event = random.choices(available_events, weights=weights, k=1)[0]

        # Update history
        RandomEvent._last_events.append(selected_event["title"])
        if len(RandomEvent._last_events) > RandomEvent._max_history:
            RandomEvent._last_events.pop(0)

        logger.info(f"Selected random event: {selected_event['title']}")
        return selected_event

    @staticmethod
    def create_random_event() -> 'RandomEvent':
        """Create a random event.

        Returns:
            RandomEvent: A randomly generated event
        """
        template = RandomEvent.get_random_event()
        return RandomEvent.create_from_template(template)
