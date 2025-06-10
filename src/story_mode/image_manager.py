import os
import json
import logging
from typing import Optional, Dict, List, Union

logger = logging.getLogger('tokugawa_bot')

class ImageManager:
    """
    Manages images for the story mode.
    """

    def __init__(self, config_path: str = "data/story_mode/narrative/image_config.json"):
        """
        Initialize the image manager.

        Args:
            config_path (str): Path to the image configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.base_path = self.config.get("base_path", "assets/images")
        self.fallback_image = self.config.get("fallback_image", "image_not_found.png")

    def _load_config(self) -> Dict:
        """
        Load the image configuration from the JSON file.

        Returns:
            Dict: The image configuration.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Image configuration file not found at {self.config_path}. Creating default configuration.")
            return self._create_default_config()
        except json.JSONDecodeError:
            logger.error(f"Error decoding image configuration file at {self.config_path}. Using default configuration.")
            return self._create_default_config()

    def _create_default_config(self) -> Dict:
        """
        Create a default image configuration.

        Returns:
            Dict: The default image configuration.
        """
        config = {
            "base_path": "assets/images",
            "fallback_image": "image_not_found.png",
            "categories": {
                "characters": {
                    "path": "characters",
                    "expressions": {
                        "default": "default.png",
                        "happy": "happy.png",
                        "sad": "sad.png",
                        "angry": "angry.png",
                        "surprised": "surprised.png",
                        "thinking": "thinking.png"
                    }
                },
                "locations": {
                    "path": "locations",
                    "types": {
                        "academy": "academy_entrance.png",
                        "classroom": "classroom.png",
                        "dormitory": "dormitory.png",
                        "training_field": "training_field.png",
                        "library": "library.png",
                        "cafeteria": "cafeteria.png",
                        "garden": "garden.png",
                        "dojo": "dojo.png",
                        "headmaster_office": "headmaster_office.png"
                    }
                }
            }
        }

        # Save the default configuration
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

        return config

    def get_image_path(self, image_id: str, category: Optional[str] = None, subcategory: Optional[str] = None) -> str:
        """
        Get the path to an image.

        Args:
            image_id (str): The ID of the image.
            category (Optional[str]): The category of the image.
            subcategory (Optional[str]): The subcategory of the image.

        Returns:
            str: The path to the image.
        """
        if category and category in self.config["categories"]:
            category_config = self.config["categories"][category]
            category_path = category_config["path"]

            if subcategory and subcategory in category_config:
                subcategory_config = category_config[subcategory]
                if isinstance(subcategory_config, dict) and image_id in subcategory_config:
                    return os.path.join(self.base_path, category_path, subcategory_config[image_id])

            # Check if the image_id is a direct key in the category
            if isinstance(category_config, dict) and image_id in category_config:
                return os.path.join(self.base_path, category_path, category_config[image_id])

        # If no category or subcategory is specified, or if the image is not found,
        # try to find the image in all categories
        for category_name, category_config in self.config["categories"].items():
            category_path = category_config["path"]
            if isinstance(category_config, dict):
                for key, value in category_config.items():
                    if isinstance(value, dict) and image_id in value:
                        return os.path.join(self.base_path, category_path, value[image_id])
                    elif key == image_id:
                        return os.path.join(self.base_path, category_path, value)

        # If the image is not found, return the fallback image
        return os.path.join(self.base_path, self.fallback_image)

    def get_character_image(self, character_id: str, expression: str = "default") -> str:
        """
        Get the path to a character image.

        Args:
            character_id (str): The ID of the character.
            expression (str): The expression of the character.

        Returns:
            str: The path to the character image.
        """
        return self.get_image_path(character_id, "characters", "expressions")

    def get_location_image(self, location_id: str, location_type: str = "default") -> str:
        """
        Get the path to a location image.

        Args:
            location_id (str): The ID of the location.
            location_type (str): The type of the location.

        Returns:
            str: The path to the location image.
        """
        return self.get_image_path(location_id, "locations", "types")

    def get_romance_image(self, scene_type: str, scene_index: int = 0) -> str:
        """
        Get the path to a romance scene image.

        Args:
            scene_type (str): The type of the romance scene.
            scene_index (int): The index of the scene.

        Returns:
            str: The path to the romance scene image.
        """
        return self.get_image_path(scene_type, "romance", "scenes")

    def get_battle_image(self, element: str) -> str:
        """
        Get the path to a battle image.

        Args:
            element (str): The element of the battle.

        Returns:
            str: The path to the battle image.
        """
        return self.get_image_path(element, "battle", "elements")

    def get_event_image(self, event_type: str) -> str:
        """
        Get the path to an event image.

        Args:
            event_type (str): The type of the event.

        Returns:
            str: The path to the event image.
        """
        return self.get_image_path(event_type, "events", "types")

    def get_npc_image(self, npc_id: str) -> str:
        """
        Get the path to an NPC image.

        Args:
            npc_id (str): The ID of the NPC.

        Returns:
            str: The path to the NPC image.
        """
        return self.get_image_path(npc_id, "npcs", "characters")

    def validate_image(self, image_path: str) -> bool:
        """
        Validate if an image exists and is not too large.

        Args:
            image_path (str): The path to the image.

        Returns:
            bool: True if the image is valid, False otherwise.
        """
        if not os.path.exists(image_path):
            logger.warning(f"Image file not found: {image_path}")
            return False

        try:
            file_size = os.path.getsize(image_path)
            if file_size > 8 * 1024 * 1024:  # 8MB limit
                logger.warning(f"Image file too large ({file_size / 1024 / 1024:.2f}MB): {image_path}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating image {image_path}: {str(e)}")
            return False

    def list_available_expressions(self) -> List[str]:
        """
        List all available character expressions.

        Returns:
            List[str]: List of available expressions.
        """
        if "characters" in self.config["categories"] and "expressions" in self.config["categories"]["characters"]:
            return list(self.config["categories"]["characters"]["expressions"].keys())
        return []

    def list_available_locations(self) -> List[str]:
        """
        List all available locations.

        Returns:
            List[str]: List of available locations.
        """
        if "locations" in self.config["categories"] and "types" in self.config["categories"]["locations"]:
            return list(self.config["categories"]["locations"]["types"].keys())
        return []

    def list_available_romance_scenes(self) -> List[str]:
        """
        List all available romance scenes.

        Returns:
            List[str]: List of available romance scenes.
        """
        if "romance" in self.config["categories"] and "scenes" in self.config["categories"]["romance"]:
            return list(self.config["categories"]["romance"]["scenes"].keys())
        return []

    def list_available_battle_elements(self) -> List[str]:
        """
        List all available battle elements.

        Returns:
            List[str]: List of available battle elements.
        """
        if "battle" in self.config["categories"] and "elements" in self.config["categories"]["battle"]:
            return list(self.config["categories"]["battle"]["elements"].keys())
        return []

    def list_available_events(self) -> List[str]:
        """
        List all available events.

        Returns:
            List[str]: List of available events.
        """
        if "events" in self.config["categories"] and "types" in self.config["categories"]["events"]:
            return list(self.config["categories"]["events"]["types"].keys())
        return []

    def list_available_npcs(self) -> List[str]:
        """
        List all available NPCs.

        Returns:
            List[str]: List of available NPCs.
        """
        if "npcs" in self.config["categories"] and "characters" in self.config["categories"]["npcs"]:
            return list(self.config["categories"]["npcs"]["characters"].keys())
        return [] 