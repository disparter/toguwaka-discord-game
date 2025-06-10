from typing import Dict, List, Any, Optional
import json
import logging
import os
from .interfaces import Chapter
from .chapter import StoryChapter, ChallengeChapter, BranchingChapter
from .npc import NPCManager
from .progress import DefaultStoryProgressManager
from .story_consequences import DynamicConsequencesSystem
from .powers import PowerEvolutionSystem
from .seasonal_events import SeasonalEventSystem
from .companions import CompanionSystem
from .narrative_logger import get_narrative_logger
from .validation import get_story_validator, validate_story_data
from .arcs.arc_manager import ArcManager
from .image_processor import ImageProcessor
from pathlib import Path
from .event_manager import ConcreteEventManager
from .club_rivalry_system import ClubSystem
from .club_content import ClubContentManager
from .player_manager import PlayerManager
from .choice_processor import ChoiceProcessor
from .image_manager import ImageManager

logger = logging.getLogger('tokugawa_bot')

class StoryMode:
    """
    Main class for managing the story mode.
    """

    def __init__(self):
        """
        Initialize the story mode.
        """
        self.story_data = self._load_story_data()
        self.image_manager = ImageManager()
        logger.info("StoryMode initialized")

    def _load_story_data(self) -> Dict:
        """
        Load the story data from the JSON file.

        Returns:
            Dict: The story data.
        """
        try:
            with open("data/story_mode/narrative/index.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Story data file not found")
            return {}
        except json.JSONDecodeError:
            logger.error("Error decoding story data file")
            return {}

    def start_story(self, player_data: Dict) -> Dict:
        """
        Start or continue the story for a player.

        Args:
            player_data (Dict): The player's data.

        Returns:
            Dict: The result of starting the story.
        """
        try:
            # Get the current chapter ID from the player's story progress
            story_progress = player_data.get("story_progress", {})
            current_chapter_id = story_progress.get("current_chapter")

            # If no current chapter, start from the beginning
            if not current_chapter_id:
                current_chapter_id = "1_1_arrival"

            # Load the chapter
            chapter = self._load_chapter(current_chapter_id)
            if not chapter:
                return {"error": f"Chapter {current_chapter_id} not found"}

            # Process the chapter
            result = chapter.process(player_data)
            if "error" in result:
                return result

            # Update the player's story progress
            player_data["story_progress"] = result.get("player_data", {}).get("story_progress", {})

            # Add the chapter data to the result
            result["chapter_data"] = chapter

            return result

        except Exception as e:
            logger.error(f"Error starting story: {str(e)}")
            return {"error": f"Error starting story: {str(e)}"}

    def _load_chapter(self, chapter_id: str) -> Optional[StoryChapter]:
        """
        Load a chapter from the JSON file.

        Args:
            chapter_id (str): The ID of the chapter to load.

        Returns:
            Optional[StoryChapter]: The loaded chapter, or None if not found.
        """
        try:
            # Get the chapter path from the story data
            chapter_path = self.story_data.get("chapters", {}).get(chapter_id, {}).get("path")
            if not chapter_path:
                logger.error(f"Chapter path not found for chapter {chapter_id}")
                return None

            # Load the chapter file
            with open(chapter_path, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)

            # Create a new StoryChapter instance
            return StoryChapter(chapter_id, chapter_data, self.image_manager)

        except FileNotFoundError:
            logger.error(f"Chapter file not found: {chapter_path}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error decoding chapter file: {chapter_path}")
            return None
        except Exception as e:
            logger.error(f"Error loading chapter {chapter_id}: {str(e)}")
            return None

    def process_choice(self, player_data: Dict, choice_index: int) -> Dict:
        """
        Process a player's choice in the story.

        Args:
            player_data (Dict): The player's data.
            choice_index (int): The index of the choice made.

        Returns:
            Dict: The result of processing the choice.
        """
        try:
            # Get the current chapter ID from the player's story progress
            story_progress = player_data.get("story_progress", {})
            current_chapter_id = story_progress.get("current_chapter")

            # If no current chapter, return an error
            if not current_chapter_id:
                return {"error": "No current chapter found"}

            # Load the chapter
            chapter = self._load_chapter(current_chapter_id)
            if not chapter:
                return {"error": f"Chapter {current_chapter_id} not found"}

            # Process the choice
            result = chapter.process_choice(player_data, choice_index)
            if "error" in result:
                return result

            # Update the player's story progress
            player_data["story_progress"] = result.get("player_data", {}).get("story_progress", {})

            # Add the chapter data to the result
            result["chapter_data"] = chapter

            return result

        except Exception as e:
            logger.error(f"Error processing choice: {str(e)}")
            return {"error": f"Error processing choice: {str(e)}"}

    def get_available_events(self, player_data: Dict) -> List[Dict]:
        """
        Get the available events for a player.

        Args:
            player_data (Dict): The player's data.

        Returns:
            List[Dict]: The list of available events.
        """
        try:
            # Get the current chapter ID from the player's story progress
            story_progress = player_data.get("story_progress", {})
            current_chapter_id = story_progress.get("current_chapter")

            # If no current chapter, return an empty list
            if not current_chapter_id:
                return []

            # Load the chapter
            chapter = self._load_chapter(current_chapter_id)
            if not chapter:
                return []

            # Get the available events
            return chapter.get_available_events(player_data)

        except Exception as e:
            logger.error(f"Error getting available events: {str(e)}")
            return []

    def validate_story(self) -> List[str]:
        """
        Validate the story data.

        Returns:
            List[str]: List of validation errors.
        """
        return validate_story_data(self.story_data)

    def get_chapter_info(self, chapter_id: str) -> Optional[Dict]:
        """
        Get information about a chapter.

        Args:
            chapter_id (str): The ID of the chapter.

        Returns:
            Optional[Dict]: The chapter information, or None if not found.
        """
        return self.story_data.get("chapters", {}).get(chapter_id)

    def get_next_chapter(self, current_chapter_id: str) -> Optional[str]:
        """
        Get the next chapter ID.

        Args:
            current_chapter_id (str): The current chapter ID.

        Returns:
            Optional[str]: The next chapter ID, or None if not found.
        """
        chapter_info = self.get_chapter_info(current_chapter_id)
        if not chapter_info:
            return None

        return chapter_info.get("next_chapter")

    def get_previous_chapter(self, current_chapter_id: str) -> Optional[str]:
        """
        Get the previous chapter ID.

        Args:
            current_chapter_id (str): The current chapter ID.

        Returns:
            Optional[str]: The previous chapter ID, or None if not found.
        """
        chapter_info = self.get_chapter_info(current_chapter_id)
        if not chapter_info:
            return None

        return chapter_info.get("previous_chapter")

    def get_chapter_requirements(self, chapter_id: str) -> Dict:
        """
        Get the requirements for a chapter.

        Args:
            chapter_id (str): The ID of the chapter.

        Returns:
            Dict: The chapter requirements.
        """
        chapter_info = self.get_chapter_info(chapter_id)
        if not chapter_info:
            return {}

        return chapter_info.get("requirements", {})

    def check_chapter_requirements(self, player_data: Dict, chapter_id: str) -> bool:
        """
        Check if a player meets the requirements for a chapter.

        Args:
            player_data (Dict): The player's data.
            chapter_id (str): The ID of the chapter.

        Returns:
            bool: True if the player meets the requirements, False otherwise.
        """
        requirements = self.get_chapter_requirements(chapter_id)
        if not requirements:
            return True

        # Check level requirement
        if "level" in requirements:
            if player_data.get("level", 0) < requirements["level"]:
                return False

        # Check element requirement
        if "element" in requirements:
            if player_data.get("element") != requirements["element"]:
                return False

        # Check completed chapters requirement
        if "completed_chapters" in requirements:
            story_progress = player_data.get("story_progress", {})
            completed_chapters = story_progress.get("completed_chapters", [])
            for required_chapter in requirements["completed_chapters"]:
                if required_chapter not in completed_chapters:
                    return False

        return True

    def get_available_chapters(self, player_data: Dict) -> List[str]:
        """
        Get the list of chapters available to a player.

        Args:
            player_data (Dict): The player's data.

        Returns:
            List[str]: The list of available chapter IDs.
        """
        available_chapters = []
        for chapter_id in self.story_data.get("chapters", {}):
            if self.check_chapter_requirements(player_data, chapter_id):
                available_chapters.append(chapter_id)

        return available_chapters

    def get_chapter_progress(self, player_data: Dict, chapter_id: str) -> Dict:
        """
        Get the progress of a player in a chapter.

        Args:
            player_data (Dict): The player's data.
            chapter_id (str): The ID of the chapter.

        Returns:
            Dict: The chapter progress.
        """
        story_progress = player_data.get("story_progress", {})
        chapter_progress = story_progress.get("chapter_progress", {}).get(chapter_id, {})

        return {
            "completed": chapter_id in story_progress.get("completed_chapters", []),
            "current_scene": chapter_progress.get("current_scene"),
            "choices_made": chapter_progress.get("choices_made", []),
            "events_completed": chapter_progress.get("events_completed", []),
            "items_collected": chapter_progress.get("items_collected", []),
            "npcs_met": chapter_progress.get("npcs_met", []),
            "locations_visited": chapter_progress.get("locations_visited", [])
        }

    def get_story_progress(self, player_data: Dict) -> Dict:
        """
        Get the overall story progress of a player.

        Args:
            player_data (Dict): The player's data.

        Returns:
            Dict: The story progress.
        """
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
        total_chapters = len(self.story_data.get("chapters", {}))

        return {
            "current_chapter": story_progress.get("current_chapter"),
            "completed_chapters": completed_chapters,
            "total_chapters": total_chapters,
            "completion_percentage": (len(completed_chapters) / total_chapters * 100) if total_chapters > 0 else 0,
            "chapter_progress": {
                chapter_id: self.get_chapter_progress(player_data, chapter_id)
                for chapter_id in self.story_data.get("chapters", {})
            }
        } 