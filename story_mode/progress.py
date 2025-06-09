from typing import Dict, List, Any, Optional, Union, TypedDict, Callable
import json
import logging
from .interfaces import StoryProgressManager

logger = logging.getLogger('tokugawa_bot')

# Type definitions for better type hinting
class StoryProgress(TypedDict, total=False):
    current_year: int
    current_chapter: int
    current_challenge_chapter: Optional[str]
    full_chapter_id: Optional[str]  # Stores the full chapter ID including suffixes like _success or _failure
    completed_chapters: List[str]
    completed_challenge_chapters: List[str]
    failed_challenge_chapters: List[str]
    blocked_chapter_arcs: List[str]
    available_chapters: List[str]
    club_progress: Dict[str, Any]
    villain_defeats: List[str]
    minion_defeats: List[str]
    hierarchy_tier: int
    hierarchy_points: int
    discovered_secrets: List[str]
    special_items: List[str]
    character_relationships: Dict[str, Any]
    story_choices: Dict[str, Dict[str, Any]]
    triggered_events: Dict[str, Any]

# Default values for story progress initialization
DEFAULT_STORY_PROGRESS: StoryProgress = {
    "current_year": 1,
    "current_chapter": 1,
    "current_challenge_chapter": None,
    "full_chapter_id": None,  # New field to store the full chapter ID including suffixes
    "completed_chapters": [],
    "completed_challenge_chapters": [],
    "failed_challenge_chapters": [],
    "blocked_chapter_arcs": [],
    "available_chapters": [],
    "club_progress": {},
    "villain_defeats": [],
    "minion_defeats": [],
    "hierarchy_tier": 0,
    "hierarchy_points": 0,
    "discovered_secrets": [],
    "special_items": [],
    "character_relationships": {},
    "story_choices": {},
    "triggered_events": {}
}

class DefaultStoryProgressManager(StoryProgressManager):
    """
    Default implementation of the StoryProgressManager interface.
    Manages a player's progress through the story mode.
    """
    def __init__(self):
        """Initialize the story progress manager."""
        pass

    def _get_story_progress(self, player_data: Dict[str, Any]) -> StoryProgress:
        """
        Helper method to get story progress from player data.

        Args:
            player_data: The player data dictionary

        Returns:
            The story progress dictionary
        """
        return player_data.get("story_progress", {})

    def _update_story_progress(self, player_data: Dict[str, Any], story_progress: StoryProgress) -> Dict[str, Any]:
        """
        Helper method to update story progress in player data.

        Args:
            player_data: The player data dictionary
            story_progress: The updated story progress dictionary

        Returns:
            The updated player data dictionary
        """
        player_data["story_progress"] = story_progress
        return player_data

    def _get_list_from_progress(self, player_data: Dict[str, Any], key: str) -> List[str]:
        """
        Helper method to get a list from story progress.

        Args:
            player_data: The player data dictionary
            key: The key for the list in story progress

        Returns:
            The list from story progress
        """
        story_progress = self._get_story_progress(player_data)
        return story_progress.get(key, [])

    def _add_to_list_in_progress(self, player_data: Dict[str, Any], key: str, value: str) -> Dict[str, Any]:
        """
        Helper method to add a value to a list in story progress if it doesn't exist.

        Args:
            player_data: The player data dictionary
            key: The key for the list in story progress
            value: The value to add to the list

        Returns:
            The updated player data dictionary
        """
        story_progress = self._get_story_progress(player_data)
        items_list = story_progress.get(key, [])

        if value not in items_list:
            items_list.append(value)
            story_progress[key] = items_list

            user_id = player_data.get('user_id', 'unknown')
            logger.info(f"Added {value} to {key} for player {user_id}")

        return self._update_story_progress(player_data, story_progress)

    def _log_with_player_context(self, message: str, player_data: Dict[str, Any], level: str = "info") -> None:
        """
        Helper method to log messages with player context.

        Args:
            message: The message to log
            player_data: The player data dictionary
            level: The log level (info, debug, error, warning)
        """
        user_id = player_data.get('user_id', 'unknown')
        full_message = f"{message} for player {user_id}"

        if level == "debug":
            logger.debug(full_message)
        elif level == "error":
            logger.error(full_message)
        elif level == "warning":
            logger.warning(full_message)
        else:
            logger.info(full_message)

    def get_current_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the ID of the player's current chapter.

        Args:
            player_data: The player data dictionary

        Returns:
            The ID of the current chapter or None if no chapter is in progress
        """
        story_progress = self._get_story_progress(player_data)

        # First check if there's a full chapter ID stored (including suffixes like _success or _failure)
        full_chapter_id = story_progress.get("full_chapter_id")
        if full_chapter_id:
            return full_chapter_id

        # If there's a challenge chapter in progress, return that instead
        current_challenge_chapter = story_progress.get("current_challenge_chapter")
        if current_challenge_chapter:
            return current_challenge_chapter

        # Fallback to constructing the chapter ID from year and chapter number
        current_year = story_progress.get("current_year", 1)
        current_chapter = story_progress.get("current_chapter", 1)
        return f"{current_year}_{current_chapter}"

    def set_current_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Sets the player's current chapter and returns updated player data.

        Args:
            player_data: The player data dictionary
            chapter_id: The ID of the chapter to set as current

        Returns:
            The updated player data dictionary

        Raises:
            ValueError: If the chapter ID format is invalid
        """
        story_progress = self._get_story_progress(player_data)

        # Store the full chapter ID including any suffixes
        story_progress["full_chapter_id"] = chapter_id

        # Parse chapter ID to get year and chapter number if it's in the format "year_chapter"
        if "_" in chapter_id:
            try:
                parts = chapter_id.split("_")
                # Check if the first part is a number (year)
                if parts[0].isdigit() and parts[1].isdigit():
                    year = parts[0]
                    chapter = parts[1]
                    story_progress["current_year"] = int(year)
                    story_progress["current_chapter"] = int(chapter)
                else:
                    # If it's not in "year_chapter" format, treat it as a challenge/special chapter
                    story_progress["current_challenge_chapter"] = chapter_id
            except (IndexError, ValueError):
                # If there's any error in parsing, treat it as a challenge/special chapter
                story_progress["current_challenge_chapter"] = chapter_id
        else:
            # If no underscore, assume it's a challenge chapter
            story_progress["current_challenge_chapter"] = chapter_id

        self._log_with_player_context(f"Set current chapter to {chapter_id}", player_data)

        return self._update_story_progress(player_data, story_progress)

    def complete_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Marks a chapter as completed and returns updated player data.

        Args:
            player_data: The player data dictionary
            chapter_id: The ID of the chapter to mark as completed

        Returns:
            The updated player data dictionary
        """
        story_progress = self._get_story_progress(player_data)

        # Add to completed chapters
        if "_" in chapter_id:  # Regular chapter
            # Add to completed chapters list
            if chapter_id not in story_progress.get("completed_chapters", []):
                player_data = self._add_to_list_in_progress(player_data, "completed_chapters", chapter_id)
                story_progress = self._get_story_progress(player_data)  # Get updated story progress

            # Clear current chapter if it matches the completed one
            if (story_progress.get("current_year") == int(chapter_id.split("_")[0]) and 
                story_progress.get("current_chapter") == int(chapter_id.split("_")[1])):
                # Don't clear yet, will be updated when next chapter is set
                pass

            # Clear full_chapter_id if it matches the completed one
            if story_progress.get("full_chapter_id") == chapter_id:
                story_progress["full_chapter_id"] = None
                player_data = self._update_story_progress(player_data, story_progress)
        else:  # Challenge chapter
            # Add to completed challenge chapters list
            if chapter_id not in story_progress.get("completed_challenge_chapters", []):
                player_data = self._add_to_list_in_progress(player_data, "completed_challenge_chapters", chapter_id)
                story_progress = self._get_story_progress(player_data)  # Get updated story progress

            # Clear current challenge chapter
            if story_progress.get("current_challenge_chapter") == chapter_id:
                story_progress["current_challenge_chapter"] = None
                player_data = self._update_story_progress(player_data, story_progress)

        self._log_with_player_context(f"Completed chapter {chapter_id}", player_data)

        return player_data

    def record_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_value: Any) -> Dict[str, Any]:
        """
        Records a player's choice and returns updated player data.

        Args:
            player_data: The player data dictionary
            chapter_id: The ID of the chapter where the choice was made
            choice_key: The key identifying the choice
            choice_value: The value of the choice

        Returns:
            The updated player data dictionary
        """
        story_progress = self._get_story_progress(player_data)

        # Initialize story choices if not present
        if "story_choices" not in story_progress:
            story_progress["story_choices"] = {}

        # Initialize chapter choices if not present
        if chapter_id not in story_progress["story_choices"]:
            story_progress["story_choices"][chapter_id] = {}

        # Record the choice
        story_progress["story_choices"][chapter_id][choice_key] = choice_value

        self._log_with_player_context(
            f"Recorded choice {choice_key}={choice_value} in chapter {chapter_id}", 
            player_data, 
            "debug"
        )

        return self._update_story_progress(player_data, story_progress)

    def get_completed_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs completed by the player.

        Args:
            player_data: The player data dictionary

        Returns:
            A list of completed chapter IDs
        """
        return self._get_list_from_progress(player_data, "completed_chapters")

    def get_completed_challenge_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of challenge chapter IDs completed by the player.

        Args:
            player_data: The player data dictionary

        Returns:
            A list of completed challenge chapter IDs
        """
        return self._get_list_from_progress(player_data, "completed_challenge_chapters")

    def _get_completed_chapters_by_type(self, player_data: Dict[str, Any], chapter_type: str = "regular") -> List[str]:
        """
        Helper method to get completed chapters by type.

        Args:
            player_data: The player data dictionary
            chapter_type: The type of chapters to get ("regular" or "challenge")

        Returns:
            A list of completed chapter IDs of the specified type
        """
        key = "completed_chapters" if chapter_type == "regular" else "completed_challenge_chapters"
        return self._get_list_from_progress(player_data, key)

    def get_story_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str) -> Optional[Any]:
        """
        Returns a player's choice for a specific chapter and key.

        Args:
            player_data: The player data dictionary
            chapter_id: The ID of the chapter
            choice_key: The key identifying the choice

        Returns:
            The value of the choice or None if not found
        """
        story_progress = self._get_story_progress(player_data)
        story_choices = story_progress.get("story_choices", {})
        chapter_choices = story_choices.get(chapter_id, {})
        return chapter_choices.get(choice_key)

    def get_all_story_choices(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Returns all story choices made by the player.

        Args:
            player_data: The player data dictionary

        Returns:
            A dictionary mapping chapter IDs to choice dictionaries
        """
        story_progress = self._get_story_progress(player_data)
        return story_progress.get("story_choices", {})

    def get_next_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs that are available to the player next.

        Args:
            player_data: The player data dictionary

        Returns:
            A list of chapter IDs available to the player
        """
        story_progress = self._get_story_progress(player_data)
        completed_chapters = self._get_list_from_progress(player_data, "completed_chapters")
        available_chapters = story_progress.get("available_chapters", [])

        # Add the next sequential chapter if applicable
        current_year = story_progress.get("current_year", 1)
        current_chapter = story_progress.get("current_chapter", 1)
        next_chapter = f"{current_year}_{current_chapter + 1}"

        # Combine all available chapters
        all_available = list(set(available_chapters + [next_chapter]))

        # Filter out completed chapters
        return [chapter for chapter in all_available if chapter not in completed_chapters]

    def initialize_story_progress(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initializes story progress for a new player.

        Args:
            player_data: The player data dictionary

        Returns:
            The updated player data dictionary with initialized story progress
        """
        if "story_progress" not in player_data or not player_data["story_progress"]:
            # Use the default story progress dictionary
            player_data["story_progress"] = DEFAULT_STORY_PROGRESS.copy()
            self._log_with_player_context("Initialized story progress", player_data)
        else:
            # Ensure new fields exist in existing player data
            story_progress = self._get_story_progress(player_data)

            # Check for missing fields and add them with default values
            for key, value in DEFAULT_STORY_PROGRESS.items():
                if key not in story_progress:
                    story_progress[key] = value if not isinstance(value, (list, dict)) else value.copy()

            player_data = self._update_story_progress(player_data, story_progress)

        return player_data

    def update_hierarchy_tier(self, player_data: Dict[str, Any], new_tier: int) -> Dict[str, Any]:
        """
        Updates the player's hierarchy tier and returns updated player data.

        Args:
            player_data: The player data dictionary
            new_tier: The new hierarchy tier

        Returns:
            The updated player data dictionary
        """
        story_progress = self._get_story_progress(player_data)
        old_tier = story_progress.get("hierarchy_tier", 0)

        if new_tier != old_tier:
            story_progress["hierarchy_tier"] = new_tier
            self._log_with_player_context(f"Updated hierarchy tier: {old_tier} -> {new_tier}", player_data)

        return self._update_story_progress(player_data, story_progress)

    def add_hierarchy_points(self, player_data: Dict[str, Any], points: int) -> Dict[str, Any]:
        """
        Adds hierarchy points to the player and updates tier if necessary.

        Args:
            player_data: The player data dictionary
            points: The number of hierarchy points to add

        Returns:
            The updated player data dictionary
        """
        story_progress = self._get_story_progress(player_data)
        current_points = story_progress.get("hierarchy_points", 0)
        new_points = current_points + points

        story_progress["hierarchy_points"] = new_points

        # Check if tier should be updated
        current_tier = story_progress.get("hierarchy_tier", 0)
        new_tier = self._calculate_tier_from_points(new_points)

        if new_tier != current_tier:
            story_progress["hierarchy_tier"] = new_tier
            self._log_with_player_context(f"Updated hierarchy tier: {current_tier} -> {new_tier}", player_data)

        self._log_with_player_context(f"Added {points} hierarchy points, total: {new_points}", player_data)

        return self._update_story_progress(player_data, story_progress)

    def _calculate_tier_from_points(self, points: int) -> int:
        """
        Calculates hierarchy tier based on points.

        Args:
            points: The number of hierarchy points

        Returns:
            The calculated hierarchy tier (0-5)

        Tier levels:
        - 0: Baixo (< 10 points)
        - 1: Médio (10-24 points)
        - 2: Médio-Alto (25-49 points)
        - 3: Elite (50-74 points)
        - 4: Jack/Ás (75-99 points)
        - 5: Rei/Rainha (>= 100 points)
        """
        if points >= 100:
            return 5  # Rei/Rainha
        elif points >= 75:
            return 4  # Jack/Ás
        elif points >= 50:
            return 3  # Elite
        elif points >= 25:
            return 2  # Médio-Alto
        elif points >= 10:
            return 1  # Médio
        else:
            return 0  # Baixo

    def _add_item_to_collection(self, player_data: Dict[str, Any], collection_key: str, item_name: str, 
                              item_type: str = "item") -> Dict[str, Any]:
        """
        Generic helper method to add an item to a collection in story progress.

        Args:
            player_data: The player data dictionary
            collection_key: The key for the collection in story progress
            item_name: The name of the item to add
            item_type: The type of item (for logging purposes)

        Returns:
            The updated player data dictionary
        """
        return self._add_to_list_in_progress(player_data, collection_key, item_name)

    def discover_secret(self, player_data: Dict[str, Any], secret_name: str) -> Dict[str, Any]:
        """
        Marks a secret as discovered and returns updated player data.

        Args:
            player_data: The player data dictionary
            secret_name: The name of the secret to discover

        Returns:
            The updated player data dictionary
        """
        self._log_with_player_context(f"Discovered secret: {secret_name}", player_data)
        return self._add_item_to_collection(player_data, "discovered_secrets", secret_name, "secret")

    def add_special_item(self, player_data: Dict[str, Any], item_name: str) -> Dict[str, Any]:
        """
        Adds a special item to the player's inventory and returns updated player data.

        Args:
            player_data: The player data dictionary
            item_name: The name of the special item to add

        Returns:
            The updated player data dictionary
        """
        self._log_with_player_context(f"Added special item: {item_name}", player_data)
        return self._add_item_to_collection(player_data, "special_items", item_name, "special item")

    def save_progress(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stub method for saving player progress. Returns player_data unchanged.
        """
        return player_data
