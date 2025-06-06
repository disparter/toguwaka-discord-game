from typing import Dict, List, Any, Optional, Union
import json
import logging
from .interfaces import StoryProgressManager

logger = logging.getLogger('tokugawa_bot')

class DefaultStoryProgressManager(StoryProgressManager):
    """
    Default implementation of the StoryProgressManager interface.
    Manages a player's progress through the story mode.
    """
    def __init__(self):
        """Initialize the story progress manager."""
        pass

    def get_current_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the ID of the player's current chapter.
        """
        story_progress = player_data.get("story_progress", {})
        current_year = story_progress.get("current_year", 1)
        current_chapter = story_progress.get("current_chapter", 1)

        # If there's a challenge chapter in progress, return that instead
        current_challenge_chapter = story_progress.get("current_challenge_chapter")
        if current_challenge_chapter:
            return current_challenge_chapter

        return f"{current_year}_{current_chapter}"

    def set_current_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Sets the player's current chapter and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})

        # Parse chapter ID to get year and chapter number
        if "_" in chapter_id:
            try:
                parts = chapter_id.split("_")
                year = parts[0]
                chapter = parts[1]
                story_progress["current_year"] = int(year)
                story_progress["current_chapter"] = int(chapter)
            except IndexError:
                logger.error(f"ID do capítulo inválido: {chapter_id}. Formato esperado: 'ano_capitulo'")
                raise ValueError(f"ID inválido: {chapter_id}")
        else:
            # If no year specified, assume it's a challenge chapter
            story_progress["current_challenge_chapter"] = chapter_id

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Set current chapter to {chapter_id} for player {player_data.get('user_id')}")

        return player_data

    def complete_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Marks a chapter as completed and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})

        # Add to completed chapters
        if "_" in chapter_id:  # Regular chapter
            completed_chapters = story_progress.get("completed_chapters", [])
            if chapter_id not in completed_chapters:
                completed_chapters.append(chapter_id)
            story_progress["completed_chapters"] = completed_chapters

            # Clear current chapter if it matches the completed one
            if (story_progress.get("current_year") == int(chapter_id.split("_")[0]) and 
                story_progress.get("current_chapter") == int(chapter_id.split("_")[1])):
                # Don't clear yet, will be updated when next chapter is set
                pass
        else:  # Challenge chapter
            completed_challenge_chapters = story_progress.get("completed_challenge_chapters", [])
            if chapter_id not in completed_challenge_chapters:
                completed_challenge_chapters.append(chapter_id)
            story_progress["completed_challenge_chapters"] = completed_challenge_chapters

            # Clear current challenge chapter
            if story_progress.get("current_challenge_chapter") == chapter_id:
                story_progress["current_challenge_chapter"] = None

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Completed chapter {chapter_id} for player {player_data.get('user_id')}")

        return player_data

    def record_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_value: Any) -> Dict[str, Any]:
        """
        Records a player's choice and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})

        # Initialize story choices if not present
        if "story_choices" not in story_progress:
            story_progress["story_choices"] = {}

        # Initialize chapter choices if not present
        if chapter_id not in story_progress["story_choices"]:
            story_progress["story_choices"][chapter_id] = {}

        # Record the choice
        story_progress["story_choices"][chapter_id][choice_key] = choice_value

        # Update player data
        player_data["story_progress"] = story_progress

        logger.debug(f"Recorded choice {choice_key}={choice_value} in chapter {chapter_id} for player {player_data.get('user_id')}")

        return player_data

    def get_completed_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs completed by the player.
        """
        story_progress = player_data.get("story_progress", {})
        return story_progress.get("completed_chapters", [])

    def get_completed_challenge_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of challenge chapter IDs completed by the player.
        """
        story_progress = player_data.get("story_progress", {})
        return story_progress.get("completed_challenge_chapters", [])

    def get_story_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str) -> Optional[Any]:
        """
        Returns a player's choice for a specific chapter and key.
        """
        story_progress = player_data.get("story_progress", {})
        story_choices = story_progress.get("story_choices", {})
        chapter_choices = story_choices.get(chapter_id, {})
        return chapter_choices.get(choice_key)

    def get_all_story_choices(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Returns all story choices made by the player.
        """
        story_progress = player_data.get("story_progress", {})
        return story_progress.get("story_choices", {})

    def get_next_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs that are available to the player next.
        """
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
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
        """
        if "story_progress" not in player_data or not player_data["story_progress"]:
            player_data["story_progress"] = {
                "current_year": 1,
                "current_chapter": 1,
                "current_challenge_chapter": None,
                "completed_chapters": [],
                "completed_challenge_chapters": [],
                "failed_challenge_chapters": [],  # Track failed challenges
                "blocked_chapter_arcs": [],       # Track blocked chapter arcs
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

            logger.info(f"Initialized story progress for player {player_data.get('user_id')}")
        else:
            # Ensure new fields exist in existing player data
            story_progress = player_data["story_progress"]
            if "failed_challenge_chapters" not in story_progress:
                story_progress["failed_challenge_chapters"] = []
            if "blocked_chapter_arcs" not in story_progress:
                story_progress["blocked_chapter_arcs"] = []
            player_data["story_progress"] = story_progress

        return player_data

    def update_hierarchy_tier(self, player_data: Dict[str, Any], new_tier: int) -> Dict[str, Any]:
        """
        Updates the player's hierarchy tier and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})
        old_tier = story_progress.get("hierarchy_tier", 0)

        if new_tier != old_tier:
            story_progress["hierarchy_tier"] = new_tier
            logger.info(f"Updated hierarchy tier: {old_tier} -> {new_tier} for player {player_data.get('user_id')}")

        # Update player data
        player_data["story_progress"] = story_progress

        return player_data

    def add_hierarchy_points(self, player_data: Dict[str, Any], points: int) -> Dict[str, Any]:
        """
        Adds hierarchy points to the player and updates tier if necessary.
        """
        story_progress = player_data.get("story_progress", {})
        current_points = story_progress.get("hierarchy_points", 0)
        new_points = current_points + points

        story_progress["hierarchy_points"] = new_points

        # Check if tier should be updated
        current_tier = story_progress.get("hierarchy_tier", 0)
        new_tier = self._calculate_tier_from_points(new_points)

        if new_tier != current_tier:
            story_progress["hierarchy_tier"] = new_tier
            logger.info(f"Updated hierarchy tier: {current_tier} -> {new_tier} for player {player_data.get('user_id')}")

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Added {points} hierarchy points for player {player_data.get('user_id')}, total: {new_points}")

        return player_data

    def _calculate_tier_from_points(self, points: int) -> int:
        """
        Calculates hierarchy tier based on points.
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

    def discover_secret(self, player_data: Dict[str, Any], secret_name: str) -> Dict[str, Any]:
        """
        Marks a secret as discovered and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})
        discovered_secrets = story_progress.get("discovered_secrets", [])

        if secret_name not in discovered_secrets:
            discovered_secrets.append(secret_name)
            story_progress["discovered_secrets"] = discovered_secrets

            logger.info(f"Discovered secret: {secret_name} for player {player_data.get('user_id')}")

        # Update player data
        player_data["story_progress"] = story_progress

        return player_data

    def add_special_item(self, player_data: Dict[str, Any], item_name: str) -> Dict[str, Any]:
        """
        Adds a special item to the player's inventory and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})
        special_items = story_progress.get("special_items", [])

        if item_name not in special_items:
            special_items.append(item_name)
            story_progress["special_items"] = special_items

            logger.info(f"Added special item: {item_name} for player {player_data.get('user_id')}")

        # Update player data
        player_data["story_progress"] = story_progress

        return player_data
