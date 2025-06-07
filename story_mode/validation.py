from typing import Dict, List, Any, Optional, Union, Callable
import logging
import json
import re
from .narrative_logger import get_narrative_logger

# Set up logging
logger = logging.getLogger('tokugawa_bot')

class StoryValidator:
    """
    A class for validating story elements like choices, IDs, affinities, and conditionals.
    This helps ensure that the narrative flow is properly tracked and errors are minimized.
    """

    def __init__(self):
        """Initialize the story validator."""
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

# Singleton instance
_story_validator = None

def get_story_validator() -> StoryValidator:
    """
    Get the singleton instance of the story validator.

    Returns:
        The story validator instance
    """
    global _story_validator
    if _story_validator is None:
        _story_validator = StoryValidator()
    return _story_validator