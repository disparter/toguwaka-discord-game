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
from .validation import get_story_validator, validate_story_data, StoryValidator
from .arcs.arc_manager import ArcManager
from .image_processor import ImageProcessor
from pathlib import Path
from .event_manager import ConcreteEventManager
from .club_rivalry_system import ClubSystem
from .club_content import ClubContentManager
from .player_manager import PlayerManager
from .choice_processor import ChoiceProcessor
from .image_manager import ImageManager
import discord

logger = logging.getLogger('tokugawa_bot')

class StoryMode:
    """
    Main class for managing the story mode.
    """

    def __init__(self, data_dir: str):
        """
        Initialize the story mode.
        """
        self.data_dir = data_dir
        self.progress_manager = DefaultStoryProgressManager()
        self.validator = StoryValidator(data_dir, self.progress_manager)
        self.story_data = self._load_story_data()
        self.image_manager = ImageManager()
        logger.info("StoryMode initialized")

    def _load_story_data(self) -> Dict[str, Any]:
        """
        Load the story data from the JSON file.

        Returns:
            Dict: The story data.
        """
        try:
            story_file = os.path.join(self.data_dir, "story.json")
            if not os.path.exists(story_file):
                logger.error(f"Story file not found: {story_file}")
                return {}

            with open(story_file, "r") as f:
                story_data = json.load(f)

            return story_data
        except Exception as e:
            logger.error(f"Error loading story data: {str(e)}")
            return {}

    async def start_story(self, interaction: discord.Interaction) -> None:
        """Start the story mode for a player."""
        try:
            # Get player data
            player = await self.db.get_player(str(interaction.user.id))
            if not player:
                await interaction.response.send_message("Você precisa criar um personagem primeiro! Use `/criar` para começar.", ephemeral=True)
                return
            
            # Get current chapter
            story_progress = json.loads(player.get('story_progress', '{"current_chapter": "1_1_arrival"}'))
            current_chapter = story_progress.get('current_chapter', '1_1_arrival')
            
            # Get chapter data
            chapter = self.chapters.get(current_chapter)
            if not chapter:
                await interaction.response.send_message("Erro ao carregar o capítulo. Por favor, tente novamente mais tarde.", ephemeral=True)
                return
            
            # Create chapter embed
            embed = discord.Embed(
                title=chapter['title'],
                description=chapter['description'],
                color=discord.Color.blue()
            )
            
            # Add chapter image if available
            if chapter.get('image'):
                embed.set_image(url=chapter['image'])
            
            # Create view with choices
            view = StoryChoiceView(chapter['choices'], self)
            
            # Send chapter
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error starting story: {e}")
            await interaction.response.send_message("Ocorreu um erro ao iniciar a história. Por favor, tente novamente mais tarde.", ephemeral=True)

    async def _process_chapter(self, player_data: Dict[str, Any], chapter_data: Dict[str, Any]) -> None:
        """
        Process a chapter.

        Args:
            player_data: The player's data.
            chapter_data: The chapter data.
        """
        try:
            # Get current scene
            current_scene = chapter_data.get("scenes", [])[0]
            if not current_scene:
                logger.error("No scenes found in chapter")
                return

            # Process the scene
            await self._process_scene(player_data, current_scene)
        except Exception as e:
            logger.error(f"Error processing chapter: {str(e)}")

    async def _process_scene(self, player_data: Dict[str, Any], scene_data: Dict[str, Any]) -> None:
        """
        Process a scene.

        Args:
            player_data: The player's data.
            scene_data: The scene data.
        """
        try:
            # Get scene text
            scene_text = scene_data.get("text", "")
            if not scene_text:
                logger.error("No text found in scene")
                return

            # Get scene choices
            choices = scene_data.get("choices", [])
            if not choices:
                logger.error("No choices found in scene")
                return

            # Record the scene text
            for choice in choices:
                choice_key = choice.get("key")
                choice_value = choice.get("value")
                if choice_key and choice_value:
                    await self.progress_manager.record_choice(player_data, scene_data.get("id", "unknown"), choice_key, choice_value)
        except Exception as e:
            logger.error(f"Error processing scene: {str(e)}")

    def _get_first_chapter(self) -> Optional[str]:
        """
        Get the first chapter ID.

        Returns:
            The first chapter ID or None if not found.
        """
        try:
            chapters = self.story_data.get("chapters", {})
            if not chapters:
                logger.error("No chapters found in story data")
                return None

            # Get the first chapter ID
            first_chapter = next(iter(chapters))
            return first_chapter
        except Exception as e:
            logger.error(f"Error getting first chapter: {str(e)}")
            return None

    async def _load_chapter(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a chapter.

        Args:
            chapter_id: The chapter ID.

        Returns:
            The chapter data or None if not found.
        """
        try:
            chapter_file = os.path.join(self.data_dir, "chapters", f"{chapter_id}.json")
            if not os.path.exists(chapter_file):
                logger.error(f"Chapter file not found: {chapter_file}")
                return None

            with open(chapter_file, "r") as f:
                chapter_data = json.load(f)

            return chapter_data
        except Exception as e:
            logger.error(f"Error loading chapter: {str(e)}")
            return None

    async def process_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_value: Any) -> Dict[str, Any]:
        """
        Process a player's choice.

        Args:
            player_data: The player's data.
            chapter_id: The ID of the chapter.
            choice_key: The key identifying the choice.
            choice_value: The value of the choice.

        Returns:
            The updated player data.
        """
        try:
            # Validate choice
            if not await self.validator.validate_choice(player_data, chapter_id, choice_key, choice_value):
                logger.error(f"Invalid choice: {choice_key}={choice_value}")
                return player_data

            # Record choice
            player_data = await self.progress_manager.record_choice(player_data, chapter_id, choice_key, choice_value)

            # Check if chapter is complete
            if await self.validator.validate_chapter_completion(player_data, chapter_id):
                player_data = await self.progress_manager.complete_chapter(player_data, chapter_id)

                # Get next chapter
                next_chapters = await self.progress_manager.get_next_available_chapters(player_data)
                if next_chapters:
                    next_chapter = next_chapters[0]
                    player_data = await self.progress_manager.set_current_chapter(player_data, next_chapter)

                    # Load next chapter
                    chapter_data = await self._load_chapter(next_chapter)
                    if chapter_data:
                        await self._process_chapter(player_data, chapter_data)

            return player_data
        except Exception as e:
            logger.error(f"Error processing choice: {str(e)}")
            return player_data

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