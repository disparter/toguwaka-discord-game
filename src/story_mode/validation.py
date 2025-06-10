from typing import Dict, List, Any, Optional, Union, Callable
import logging
import json
import re
from .narrative_logger import get_narrative_logger
from pathlib import Path
import os
from story_mode.image_manager import ImageManager

# Set up logging
logger = logging.getLogger('tokugawa_bot')

class StoryValidator:
    """
    A class for validating story elements like choices, IDs, affinities, and conditionals.
    This helps ensure that the narrative flow is properly tracked and errors are minimized.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the story validator.

        Args:
            data_dir: Path to the data directory containing story mode files
        """
        self.data_dir = Path(data_dir)
        self.narrative_dir = self.data_dir / "story_mode" / "narrative"
        self.chapters_dir = self.narrative_dir / "chapters"
        self.narrative_logger = get_narrative_logger()

    def validate_chapter_id(self, chapter_id: str) -> bool:
        """
        Validate a chapter ID.

        Args:
            chapter_id: The chapter ID to validate

        Returns:
            True if the chapter ID is valid, False otherwise
        """
        # Chapter IDs should follow the pattern year_chapter or year_chapter_suffix
        pattern = r'^\d+_\d+(_[a-zA-Z0-9_]+)?$'
        is_valid = bool(re.match(pattern, chapter_id))
        
        if not is_valid:
            logger.warning(f"Invalid chapter ID format: {chapter_id}")
        
        return is_valid

    def validate_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_index: int, 
                       available_choices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a player's choice.

        Args:
            player_data: The player data
            chapter_id: The chapter ID
            choice_index: The index of the chosen option
            available_choices: The list of available choices

        Returns:
            A dictionary with validation result and error message if any
        """
        player_id = player_data.get('user_id', 'unknown')
        result = {"valid": True, "error": None}
        
        # Check if choice_index is within range
        if choice_index < 0 or choice_index >= len(available_choices):
            error_msg = f"Choice index {choice_index} is out of range (0-{len(available_choices)-1})"
            logger.warning(f"Invalid choice: {error_msg}")
            
            # Log the validation error
            self.narrative_logger.log_validation_error(
                player_id,
                chapter_id,
                "choice_index_out_of_range",
                {"choice_index": choice_index, "available_choices": len(available_choices)}
            )
            
            result["valid"] = False
            result["error"] = error_msg
            return result
        
        # Check if the choice has required metadata
        choice = available_choices[choice_index]
        if "metadata" not in choice and "next_chapter" not in choice and "next_dialogue" not in choice:
            error_msg = f"Choice at index {choice_index} is missing required metadata"
            logger.warning(f"Invalid choice: {error_msg}")
            
            # Log the validation error
            self.narrative_logger.log_validation_error(
                player_id,
                chapter_id,
                "missing_choice_metadata",
                {"choice_index": choice_index, "choice_text": choice.get("text", "")}
            )
            
            result["valid"] = False
            result["error"] = error_msg
            return result
        
        return result

    def validate_affinity_change(self, player_data: Dict[str, Any], npc_name: str, change: int) -> Dict[str, Any]:
        """
        Validate an affinity change.

        Args:
            player_data: The player data
            npc_name: The name of the NPC
            change: The amount to change affinity by

        Returns:
            A dictionary with validation result and error message if any
        """
        player_id = player_data.get('user_id', 'unknown')
        result = {"valid": True, "error": None}
        
        # Check if NPC name is valid (not empty)
        if not npc_name:
            error_msg = "NPC name cannot be empty"
            logger.warning(f"Invalid affinity change: {error_msg}")
            
            # Log the validation error
            self.narrative_logger.log_validation_error(
                player_id,
                "unknown",
                "empty_npc_name",
                {"change": change}
            )
            
            result["valid"] = False
            result["error"] = error_msg
            return result
        
        # Check if change is within reasonable bounds (-10 to 10)
        if change < -10 or change > 10:
            error_msg = f"Affinity change {change} is outside reasonable bounds (-10 to 10)"
            logger.warning(f"Invalid affinity change: {error_msg}")
            
            # Log the validation error
            self.narrative_logger.log_validation_error(
                player_id,
                "unknown",
                "affinity_change_out_of_bounds",
                {"npc_name": npc_name, "change": change}
            )
            
            result["valid"] = False
            result["error"] = error_msg
            return result
        
        return result

    def validate_conditional(self, player_data: Dict[str, Any], condition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a conditional statement.

        Args:
            player_data: The player data
            condition: The conditional statement to validate

        Returns:
            A dictionary with validation result and error message if any
        """
        player_id = player_data.get('user_id', 'unknown')
        result = {"valid": True, "error": None}
        
        # Check if condition has required fields
        if "type" not in condition:
            error_msg = "Conditional is missing 'type' field"
            logger.warning(f"Invalid conditional: {error_msg}")
            
            # Log the validation error
            self.narrative_logger.log_validation_error(
                player_id,
                "unknown",
                "missing_conditional_type",
                {"condition": condition}
            )
            
            result["valid"] = False
            result["error"] = error_msg
            return result
        
        # Validate based on condition type
        condition_type = condition["type"]
        
        if condition_type == "club_id":
            if "value" not in condition and "values" not in condition:
                error_msg = "Club ID conditional is missing 'value' or 'values' field"
                logger.warning(f"Invalid conditional: {error_msg}")
                
                # Log the validation error
                self.narrative_logger.log_validation_error(
                    player_id,
                    "unknown",
                    "missing_conditional_value",
                    {"condition_type": condition_type}
                )
                
                result["valid"] = False
                result["error"] = error_msg
                return result
        
        elif condition_type == "affinity":
            if "npc" not in condition or "threshold" not in condition:
                error_msg = "Affinity conditional is missing 'npc' or 'threshold' field"
                logger.warning(f"Invalid conditional: {error_msg}")
                
                # Log the validation error
                self.narrative_logger.log_validation_error(
                    player_id,
                    "unknown",
                    "missing_conditional_fields",
                    {"condition_type": condition_type}
                )
                
                result["valid"] = False
                result["error"] = error_msg
                return result
        
        elif condition_type == "choice":
            if "chapter_id" not in condition or "choice_key" not in condition or "choice_value" not in condition:
                error_msg = "Choice conditional is missing required fields"
                logger.warning(f"Invalid conditional: {error_msg}")
                
                # Log the validation error
                self.narrative_logger.log_validation_error(
                    player_id,
                    "unknown",
                    "missing_conditional_fields",
                    {"condition_type": condition_type}
                )
                
                result["valid"] = False
                result["error"] = error_msg
                return result
        
        return result

    def validate_chapter_data(self, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate chapter data.

        Args:
            chapter_data: The chapter data to validate

        Returns:
            A dictionary with validation result and error message if any
        """
        result = {"valid": True, "error": None, "warnings": []}
        
        # Check if chapter has required fields
        required_fields = ["title", "description"]
        for field in required_fields:
            if field not in chapter_data:
                error_msg = f"Chapter is missing required field: {field}"
                logger.warning(f"Invalid chapter data: {error_msg}")
                
                result["valid"] = False
                result["error"] = error_msg
                return result
        
        # Check if chapter has choices or dialogues
        if "choices" not in chapter_data and "dialogues" not in chapter_data:
            error_msg = "Chapter is missing both 'choices' and 'dialogues' fields"
            logger.warning(f"Invalid chapter data: {error_msg}")
            
            result["valid"] = False
            result["error"] = error_msg
            return result
        
        # Validate choices if present
        if "choices" in chapter_data:
            choices = chapter_data["choices"]
            if not isinstance(choices, list) or not choices:
                warning_msg = "Chapter has empty or invalid 'choices' field"
                logger.warning(f"Chapter data warning: {warning_msg}")
                
                result["warnings"].append(warning_msg)
            else:
                # Check each choice
                for i, choice in enumerate(choices):
                    if "text" not in choice:
                        warning_msg = f"Choice at index {i} is missing 'text' field"
                        logger.warning(f"Chapter data warning: {warning_msg}")
                        
                        result["warnings"].append(warning_msg)
                    
                    if "next_chapter" not in choice and "next_dialogue" not in choice and "metadata" not in choice:
                        warning_msg = f"Choice at index {i} is missing navigation fields"
                        logger.warning(f"Chapter data warning: {warning_msg}")
                        
                        result["warnings"].append(warning_msg)
        
        # Validate dialogues if present
        if "dialogues" in chapter_data:
            dialogues = chapter_data["dialogues"]
            if not isinstance(dialogues, list) or not dialogues:
                warning_msg = "Chapter has empty or invalid 'dialogues' field"
                logger.warning(f"Chapter data warning: {warning_msg}")
                
                result["warnings"].append(warning_msg)
            else:
                # Check each dialogue
                for i, dialogue in enumerate(dialogues):
                    if "npc" not in dialogue or "text" not in dialogue:
                        warning_msg = f"Dialogue at index {i} is missing 'npc' or 'text' field"
                        logger.warning(f"Chapter data warning: {warning_msg}")
                        
                        result["warnings"].append(warning_msg)
        
        return result

    def validate_story_structure(self) -> Dict[str, Any]:
        """
        Validate the entire story structure.

        Returns:
            Dictionary containing validation results
        """
        results = {
            "errors": [],
            "warnings": [],
            "dead_ends": [],
            "missing_assets": []
        }

        try:
            # Load story index
            story_index = self._load_story_index()
            if not story_index:
                results["errors"].append("Failed to load story index")
                return results

            # Validate main arcs
            self._validate_main_arcs(story_index, results)

            # Validate romance routes
            self._validate_romance_routes(story_index, results)

            # Validate club arcs
            self._validate_club_arcs(story_index, results)

            # Check for dead ends
            self._check_dead_ends(story_index, results)

            # Check for missing assets
            self._check_missing_assets(results)

        except Exception as e:
            results["errors"].append(f"Validation error: {str(e)}")

        return results

    def _load_story_index(self) -> Optional[Dict[str, Any]]:
        """
        Load the story index file.

        Returns:
            Story index dictionary or None if loading fails
        """
        try:
            index_path = self.narrative_dir / "index.json"
            if not index_path.exists():
                return None

            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading story index: {e}")
            return None

    def _validate_main_arcs(self, story_index: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Validate main story arcs.

        Args:
            story_index: Story index dictionary
            results: Validation results dictionary
        """
        narrative_structure = story_index.get("narrative_structure", {})
        
        for year, year_data in narrative_structure.items():
            for arc_name, arc_data in year_data.items():
                if arc_name == "intro":
                    continue  # Skip intro arcs as they're handled separately

                # Check if all required chapters exist
                chapters = arc_data.get("chapters", [])
                for chapter_id in chapters:
                    chapter_path = self.chapters_dir / f"{chapter_id}.json"
                    if not chapter_path.exists():
                        results["errors"].append(f"Missing chapter file: {chapter_id}")

                # Check requirements
                requirements = arc_data.get("requirements", {})
                if "previous_arc" in requirements:
                    prev_arc = requirements["previous_arc"]
                    if not any(prev_arc in arc for arc in year_data.values()):
                        results["errors"].append(f"Invalid previous arc reference: {prev_arc}")

    def _validate_romance_routes(self, story_index: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Validate romance routes.

        Args:
            story_index: Story index dictionary
            results: Validation results dictionary
        """
        romance_routes = story_index.get("romance_routes", {})
        
        for route_id, route_data in romance_routes.items():
            # Check if all chapters exist
            chapters = route_data.get("chapters", [])
            for chapter_id in chapters:
                chapter_path = self.chapters_dir / f"{chapter_id}.json"
                if not chapter_path.exists():
                    results["errors"].append(f"Missing romance chapter: {chapter_id}")

    def _validate_club_arcs(self, story_index: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Validate club arcs.

        Args:
            story_index: Story index dictionary
            results: Validation results dictionary
        """
        club_arcs = story_index.get("club_arcs", {})
        
        for club_id, club_data in club_arcs.items():
            # Check if all chapters exist
            chapters = club_data.get("chapters", [])
            for chapter_id in chapters:
                chapter_path = self.chapters_dir / f"{chapter_id}.json"
                if not chapter_path.exists():
                    results["errors"].append(f"Missing club chapter: {chapter_id}")

    def _check_dead_ends(self, story_index: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Check for dead ends in the story.

        Args:
            story_index: Story index dictionary
            results: Validation results dictionary
        """
        # Get all chapter files
        chapter_files = list(self.chapters_dir.glob("*.json"))
        
        for chapter_file in chapter_files:
            try:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    chapter_data = json.load(f)
                
                # Check if chapter has any connections
                has_connections = False
                
                # Check for next chapter references
                if "next_chapter" in chapter_data:
                    has_connections = True
                
                # Check for scene transitions
                scenes = chapter_data.get("scenes", [])
                for scene in scenes:
                    choices = scene.get("choices", [])
                    for choice in choices:
                        if "next_scene" in choice:
                            has_connections = True
                            break
                
                if not has_connections:
                    results["dead_ends"].append(f"Dead end found in chapter: {chapter_file.stem}")
            
            except Exception as e:
                results["errors"].append(f"Error checking dead ends in {chapter_file.name}: {e}")

    def _check_missing_assets(self, results: Dict[str, Any]) -> None:
        """
        Check for missing assets referenced in chapters.

        Args:
            results: Validation results dictionary
        """
        # Get all chapter files
        chapter_files = list(self.chapters_dir.glob("*.json"))
        
        for chapter_file in chapter_files:
            try:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    chapter_data = json.load(f)
                
                # Check backgrounds
                scenes = chapter_data.get("scenes", [])
                for scene in scenes:
                    background = scene.get("background")
                    if background:
                        bg_path = self.data_dir / "assets" / "images" / "story" / "backgrounds" / background
                        if not bg_path.exists():
                            results["missing_assets"].append(f"Missing background: {background}")
                    
                    # Check character images
                    characters = scene.get("characters", [])
                    for character in characters:
                        image = character.get("image")
                        if image:
                            char_path = self.data_dir / "assets" / "images" / "story" / "characters" / image
                            if not char_path.exists():
                                results["missing_assets"].append(f"Missing character image: {image}")
            
            except Exception as e:
                results["errors"].append(f"Error checking assets in {chapter_file.name}: {e}")

# Singleton instance
_story_validator = None

def get_story_validator(data_dir: str = "data") -> StoryValidator:
    """
    Get a story validator instance.

    Args:
        data_dir: Path to the data directory containing story mode files

    Returns:
        A StoryValidator instance
    """
    global _story_validator
    if _story_validator is None:
        _story_validator = StoryValidator(data_dir)
    return _story_validator

def validate_story_data(story_data: Dict) -> List[str]:
    """
    Validate the story data.

    Args:
        story_data (Dict): The story data to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the story data is empty
    if not story_data:
        errors.append("Story data is empty")
        return errors

    # Check if the story data has the required fields
    required_fields = ["chapters", "arcs", "romance_routes", "club_arcs"]
    for field in required_fields:
        if field not in story_data:
            errors.append(f"Missing required field: {field}")

    # Validate chapters
    if "chapters" in story_data:
        errors.extend(validate_chapters(story_data["chapters"]))

    # Validate arcs
    if "arcs" in story_data:
        errors.extend(validate_arcs(story_data["arcs"]))

    # Validate romance routes
    if "romance_routes" in story_data:
        errors.extend(validate_romance_routes(story_data["romance_routes"]))

    # Validate club arcs
    if "club_arcs" in story_data:
        errors.extend(validate_club_arcs(story_data["club_arcs"]))

    return errors

def validate_chapters(chapters: Dict) -> List[str]:
    """
    Validate the chapters.

    Args:
        chapters (Dict): The chapters to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []
    image_manager = ImageManager()

    for chapter_id, chapter_data in chapters.items():
        # Check if the chapter has the required fields
        required_fields = ["title", "description", "type", "phase", "scenes"]
        for field in required_fields:
            if field not in chapter_data:
                errors.append(f"Chapter {chapter_id} is missing required field: {field}")

        # Validate scenes
        if "scenes" in chapter_data:
            errors.extend(validate_scenes(chapter_data["scenes"], image_manager))

        # Validate requirements
        if "requirements" in chapter_data:
            errors.extend(validate_requirements(chapter_data["requirements"]))

    return errors

def validate_scenes(scenes: List[Dict], image_manager: ImageManager) -> List[str]:
    """
    Validate the scenes.

    Args:
        scenes (List[Dict]): The scenes to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    for i, scene in enumerate(scenes):
        # Check if the scene has the required fields
        required_fields = ["type"]
        for field in required_fields:
            if field not in scene:
                errors.append(f"Scene {i} is missing required field: {field}")

        # Validate scene type
        scene_type = scene.get("type")
        if scene_type == "dialogue":
            errors.extend(validate_dialogue_scene(scene, image_manager))
        elif scene_type == "choice":
            errors.extend(validate_choice_scene(scene, image_manager))
        elif scene_type == "event":
            errors.extend(validate_event_scene(scene, image_manager))
        elif scene_type == "battle":
            errors.extend(validate_battle_scene(scene, image_manager))
        elif scene_type == "romance":
            errors.extend(validate_romance_scene(scene, image_manager))
        else:
            errors.append(f"Scene {i} has unknown type: {scene_type}")

    return errors

def validate_dialogue_scene(scene: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate a dialogue scene.

    Args:
        scene (Dict): The scene to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the scene has the required fields
    if "dialogue" not in scene:
        errors.append("Dialogue scene is missing required field: dialogue")
        return errors

    dialogue = scene["dialogue"]

    # Check if the dialogue has the required fields
    required_fields = ["character", "text"]
    for field in required_fields:
        if field not in dialogue:
            errors.append(f"Dialogue is missing required field: {field}")

    # Validate character
    if "character" in dialogue:
        character = dialogue["character"]
        if "id" not in character:
            errors.append("Character is missing required field: id")
        elif "image" in character:
            image_path = image_manager.get_character_image(
                character["id"],
                character.get("expression", "default")
            )
            if not image_manager.validate_image(image_path):
                errors.append(f"Character image not found or invalid: {image_path}")

    # Validate background
    if "background" in scene:
        background = scene["background"]
        if "id" not in background:
            errors.append("Background is missing required field: id")
        else:
            image_path = image_manager.get_location_image(
                background["id"],
                background.get("type", "default")
            )
            if not image_manager.validate_image(image_path):
                errors.append(f"Background image not found or invalid: {image_path}")

    # Validate choices
    if "choices" in dialogue:
        errors.extend(validate_choices(dialogue["choices"], image_manager))

    return errors

def validate_choice_scene(scene: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate a choice scene.

    Args:
        scene (Dict): The scene to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the scene has the required fields
    required_fields = ["title", "description", "choices"]
    for field in required_fields:
        if field not in scene:
            errors.append(f"Choice scene is missing required field: {field}")

    # Validate background
    if "background" in scene:
        background = scene["background"]
        if "id" not in background:
            errors.append("Background is missing required field: id")
        else:
            image_path = image_manager.get_location_image(
                background["id"],
                background.get("type", "default")
            )
            if not image_manager.validate_image(image_path):
                errors.append(f"Background image not found or invalid: {image_path}")

    # Validate choices
    if "choices" in scene:
        errors.extend(validate_choices(scene["choices"], image_manager))

    return errors

def validate_event_scene(scene: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate an event scene.

    Args:
        scene (Dict): The scene to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the scene has the required fields
    if "event" not in scene:
        errors.append("Event scene is missing required field: event")
        return errors

    event = scene["event"]

    # Check if the event has the required fields
    required_fields = ["id", "type", "name", "description"]
    for field in required_fields:
        if field not in event:
            errors.append(f"Event is missing required field: {field}")

    # Validate event image
    if "type" in event:
        image_path = image_manager.get_event_image(event["type"])
        if not image_manager.validate_image(image_path):
            errors.append(f"Event image not found or invalid: {image_path}")

    # Validate background
    if "background" in scene:
        background = scene["background"]
        if "id" not in background:
            errors.append("Background is missing required field: id")
        else:
            image_path = image_manager.get_location_image(
                background["id"],
                background.get("type", "default")
            )
            if not image_manager.validate_image(image_path):
                errors.append(f"Background image not found or invalid: {image_path}")

    # Validate choices
    if "choices" in event:
        errors.extend(validate_choices(event["choices"], image_manager))

    return errors

def validate_battle_scene(scene: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate a battle scene.

    Args:
        scene (Dict): The scene to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the scene has the required fields
    if "battle" not in scene:
        errors.append("Battle scene is missing required field: battle")
        return errors

    battle = scene["battle"]

    # Check if the battle has the required fields
    required_fields = ["id", "element", "name", "description"]
    for field in required_fields:
        if field not in battle:
            errors.append(f"Battle is missing required field: {field}")

    # Validate battle image
    if "element" in battle:
        image_path = image_manager.get_battle_image(battle["element"])
        if not image_manager.validate_image(image_path):
            errors.append(f"Battle image not found or invalid: {image_path}")

    # Validate background
    if "background" in scene:
        background = scene["background"]
        if "id" not in background:
            errors.append("Background is missing required field: id")
        else:
            image_path = image_manager.get_location_image(
                background["id"],
                background.get("type", "default")
            )
            if not image_manager.validate_image(image_path):
                errors.append(f"Background image not found or invalid: {image_path}")

    # Validate choices
    if "choices" in battle:
        errors.extend(validate_choices(battle["choices"], image_manager))

    return errors

def validate_romance_scene(scene: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate a romance scene.

    Args:
        scene (Dict): The scene to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the scene has the required fields
    if "romance" not in scene:
        errors.append("Romance scene is missing required field: romance")
        return errors

    romance = scene["romance"]

    # Check if the romance has the required fields
    required_fields = ["id", "type", "name", "description"]
    for field in required_fields:
        if field not in romance:
            errors.append(f"Romance is missing required field: {field}")

    # Validate romance image
    if "type" in romance:
        image_path = image_manager.get_romance_image(romance["type"])
        if not image_manager.validate_image(image_path):
            errors.append(f"Romance image not found or invalid: {image_path}")

    # Validate background
    if "background" in scene:
        background = scene["background"]
        if "id" not in background:
            errors.append("Background is missing required field: id")
        else:
            image_path = image_manager.get_location_image(
                background["id"],
                background.get("type", "default")
            )
            if not image_manager.validate_image(image_path):
                errors.append(f"Background image not found or invalid: {image_path}")

    # Validate choices
    if "choices" in romance:
        errors.extend(validate_choices(romance["choices"], image_manager))

    return errors

def validate_choices(choices: List[Dict], image_manager: ImageManager) -> List[str]:
    """
    Validate the choices.

    Args:
        choices (List[Dict]): The choices to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    for i, choice in enumerate(choices):
        # Check if the choice has the required fields
        required_fields = ["text", "type"]
        for field in required_fields:
            if field not in choice:
                errors.append(f"Choice {i} is missing required field: {field}")

        # Validate choice type
        choice_type = choice.get("type")
        if choice_type == "story":
            errors.extend(validate_story_choice(choice))
        elif choice_type == "battle":
            errors.extend(validate_battle_choice(choice, image_manager))
        elif choice_type == "romance":
            errors.extend(validate_romance_choice(choice, image_manager))
        elif choice_type == "event":
            errors.extend(validate_event_choice(choice, image_manager))
        else:
            errors.append(f"Choice {i} has unknown type: {choice_type}")

    return errors

def validate_story_choice(choice: Dict) -> List[str]:
    """
    Validate a story choice.

    Args:
        choice (Dict): The choice to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the choice has effects
    if "effects" not in choice:
        errors.append("Story choice is missing required field: effects")

    return errors

def validate_battle_choice(choice: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate a battle choice.

    Args:
        choice (Dict): The choice to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the choice has the required fields
    if "battle" not in choice:
        errors.append("Battle choice is missing required field: battle")
        return errors

    battle = choice["battle"]

    # Check if the battle has the required fields
    required_fields = ["id", "element", "name", "description"]
    for field in required_fields:
        if field not in battle:
            errors.append(f"Battle is missing required field: {field}")

    # Validate battle image
    if "element" in battle:
        image_path = image_manager.get_battle_image(battle["element"])
        if not image_manager.validate_image(image_path):
            errors.append(f"Battle image not found or invalid: {image_path}")

    # Check if the battle has effects
    if "effects" not in battle:
        errors.append("Battle is missing required field: effects")

    return errors

def validate_romance_choice(choice: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate a romance choice.

    Args:
        choice (Dict): The choice to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the choice has the required fields
    if "romance" not in choice:
        errors.append("Romance choice is missing required field: romance")
        return errors

    romance = choice["romance"]

    # Check if the romance has the required fields
    required_fields = ["id", "type", "name", "description"]
    for field in required_fields:
        if field not in romance:
            errors.append(f"Romance is missing required field: {field}")

    # Validate romance image
    if "type" in romance:
        image_path = image_manager.get_romance_image(romance["type"])
        if not image_manager.validate_image(image_path):
            errors.append(f"Romance image not found or invalid: {image_path}")

    # Check if the romance has effects
    if "effects" not in romance:
        errors.append("Romance is missing required field: effects")

    return errors

def validate_event_choice(choice: Dict, image_manager: ImageManager) -> List[str]:
    """
    Validate an event choice.

    Args:
        choice (Dict): The choice to validate.
        image_manager (ImageManager): The image manager.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the choice has the required fields
    if "event" not in choice:
        errors.append("Event choice is missing required field: event")
        return errors

    event = choice["event"]

    # Check if the event has the required fields
    required_fields = ["id", "type", "name", "description"]
    for field in required_fields:
        if field not in event:
            errors.append(f"Event is missing required field: {field}")

    # Validate event image
    if "type" in event:
        image_path = image_manager.get_event_image(event["type"])
        if not image_manager.validate_image(image_path):
            errors.append(f"Event image not found or invalid: {image_path}")

    # Check if the event has effects
    if "effects" not in event:
        errors.append("Event is missing required field: effects")

    return errors

def validate_requirements(requirements: Dict) -> List[str]:
    """
    Validate the requirements.

    Args:
        requirements (Dict): The requirements to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    # Check if the requirements have valid fields
    valid_fields = ["level", "element", "completed_chapters"]
    for field in requirements:
        if field not in valid_fields:
            errors.append(f"Unknown requirement field: {field}")

    # Validate level requirement
    if "level" in requirements:
        if not isinstance(requirements["level"], int) or requirements["level"] < 1:
            errors.append("Level requirement must be a positive integer")

    # Validate element requirement
    if "element" in requirements:
        valid_elements = ["fire", "water", "earth", "air", "lightning", "ice", "light", "dark"]
        if requirements["element"] not in valid_elements:
            errors.append(f"Invalid element requirement: {requirements['element']}")

    # Validate completed chapters requirement
    if "completed_chapters" in requirements:
        if not isinstance(requirements["completed_chapters"], list):
            errors.append("Completed chapters requirement must be a list")
        else:
            for chapter_id in requirements["completed_chapters"]:
                if not isinstance(chapter_id, str):
                    errors.append("Completed chapters requirement must contain string chapter IDs")

    return errors

def validate_arcs(arcs: Dict) -> List[str]:
    """
    Validate the arcs.

    Args:
        arcs (Dict): The arcs to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    for arc_id, arc_data in arcs.items():
        # Check if the arc has the required fields
        required_fields = ["name", "description", "chapters"]
        for field in required_fields:
            if field not in arc_data:
                errors.append(f"Arc {arc_id} is missing required field: {field}")

        # Validate chapters
        if "chapters" in arc_data:
            if not isinstance(arc_data["chapters"], list):
                errors.append(f"Arc {arc_id} chapters must be a list")
            else:
                for chapter_id in arc_data["chapters"]:
                    if not isinstance(chapter_id, str):
                        errors.append(f"Arc {arc_id} chapters must contain string chapter IDs")

    return errors

def validate_romance_routes(romance_routes: Dict) -> List[str]:
    """
    Validate the romance routes.

    Args:
        romance_routes (Dict): The romance routes to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    for route_id, route_data in romance_routes.items():
        # Check if the route has the required fields
        required_fields = ["name", "description", "chapters"]
        for field in required_fields:
            if field not in route_data:
                errors.append(f"Romance route {route_id} is missing required field: {field}")

        # Validate chapters
        if "chapters" in route_data:
            if not isinstance(route_data["chapters"], list):
                errors.append(f"Romance route {route_id} chapters must be a list")
            else:
                for chapter_id in route_data["chapters"]:
                    if not isinstance(chapter_id, str):
                        errors.append(f"Romance route {route_id} chapters must contain string chapter IDs")

    return errors

def validate_club_arcs(club_arcs: Dict) -> List[str]:
    """
    Validate the club arcs.

    Args:
        club_arcs (Dict): The club arcs to validate.

    Returns:
        List[str]: List of validation errors.
    """
    errors = []

    for club_id, club_data in club_arcs.items():
        # Check if the club has the required fields
        required_fields = ["name", "description", "chapters"]
        for field in required_fields:
            if field not in club_data:
                errors.append(f"Club arc {club_id} is missing required field: {field}")

        # Validate chapters
        if "chapters" in club_data:
            if not isinstance(club_data["chapters"], list):
                errors.append(f"Club arc {club_id} chapters must be a list")
            else:
                for chapter_id in club_data["chapters"]:
                    if not isinstance(chapter_id, str):
                        errors.append(f"Club arc {club_id} chapters must contain string chapter IDs")

    return errors