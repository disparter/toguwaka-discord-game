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
from .validation import get_story_validator
from .arcs.arc_manager import ArcManager
from .image_processor import ImageProcessor
from pathlib import Path
from .event_manager import ConcreteEventManager
from .club_rivalry_system import ClubSystem
from .club_content import ClubContentManager
from .player_manager import PlayerManager
from .choice_processor import ChoiceProcessor

logger = logging.getLogger('tokugawa_bot')

class StoryMode:
    """
    Main class for the story mode system.
    Coordinates the interactions between the different components.
    """

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the story mode system.

        Args:
            base_dir: Path to the base directory containing story mode data
        """
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "story_mode"
        self.logs_dir = self.base_dir / "logs"

        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.arc_manager = ArcManager(str(self.data_dir))
        self.event_manager = ConcreteEventManager()
        self.npc_manager = NPCManager()
        self.image_processor = ImageProcessor(str(self.base_dir / "assets"))
        self.progress_manager = DefaultStoryProgressManager()
        self.consequences_system = DynamicConsequencesSystem()
        self.power_system = PowerEvolutionSystem()
        self.seasonal_event_system = SeasonalEventSystem()
        self.companion_system = CompanionSystem()
        self.club_system = ClubSystem(self.consequences_system)
        self.club_manager = ClubContentManager(base_dir)
        
        # Validate story structure
        self._validate_story_structure()

    def _validate_story_structure(self) -> None:
        """Validate the story structure and log any issues."""
        validator = get_story_validator(str(self.data_dir))
        validation_results = validator.validate_story_structure()
        
        # Log errors
        for error in validation_results.get("errors", []):
            logger.error(f"Story validation error: {error}")
            
        # Log warnings
        for warning in validation_results.get("warnings", []):
            logger.warning(f"Story validation warning: {warning}")
            
        # Log dead ends
        for dead_end in validation_results.get("dead_ends", []):
            logger.error(f"Story dead end found: {dead_end}")
            
        # Log missing assets
        for asset in validation_results.get("missing_assets", []):
            logger.warning(f"Missing story asset: {asset}")
            
        # Raise exception if there are critical errors
        if validation_results.get("errors"):
            raise ValueError("Story validation failed. Check logs for details.")

    def _load_story_structure(self) -> None:
        """Load the story structure from configuration files."""
        try:
            # Load arcs
            for arc_dir in self.arcs_dir.iterdir():
                if arc_dir.is_dir():
                    arc_name = arc_dir.name
                    arc_config = arc_dir / "config.json"

                    if arc_config.exists():
                        with open(arc_config, 'r', encoding='utf-8') as f:
                            arc_data = json.load(f)
                            self.story_structure[arc_name] = {
                                "name": arc_data.get("name", arc_name),
                                "description": arc_data.get("description", ""),
                                "chapters": []
                            }

                            # Load chapters for this arc
                            arc_chapters_dir = self.chapters_dir / arc_name
                            if arc_chapters_dir.exists():
                                for chapter_file in sorted(arc_chapters_dir.glob("*.json")):
                                    with open(chapter_file, 'r', encoding='utf-8') as cf:
                                        chapter_data = json.load(cf)
                                        self.story_structure[arc_name]["chapters"].append({
                                            "id": chapter_data.get("id"),
                                            "name": chapter_data.get("name", chapter_file.stem),
                                            "description": chapter_data.get("description", ""),
                                            "requirements": chapter_data.get("requirements", {}),
                                            "choices": chapter_data.get("choices", [])
                                        })

            logger.info("Story structure loaded successfully")
        except Exception as e:
            logger.error(f"Error loading story structure: {e}")
            self.story_structure = {}

    def validate_story_structure(self) -> bool:
        """
        Validate the story structure.

        Returns:
            True if valid, False otherwise
        """
        try:
            if not self.story_structure:
                logger.error("Story structure is empty")
                return False

            # Check each arc
            for arc_name, arc_data in self.story_structure.items():
                if not arc_data.get("chapters"):
                    logger.error(f"Arc {arc_name} has no chapters")
                    return False

                # Check each chapter
                for chapter in arc_data["chapters"]:
                    if not chapter.get("id"):
                        logger.error(f"Chapter in arc {arc_name} has no ID")
                        return False
                    if not chapter.get("choices"):
                        logger.error(f"Chapter {chapter['id']} in arc {arc_name} has no choices")
                        return False

            return True
        except Exception as e:
            logger.error(f"Error validating story structure: {e}")
            return False

    def get_available_chapters(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get available chapters for the player's current state.

        Args:
            player_data: The player's current data

        Returns:
            List of available chapters
        """
        try:
            available_chapters = []

            for arc_name, arc_data in self.story_structure.items():
                for chapter in arc_data["chapters"]:
                    # Check if chapter requirements are met
                    requirements_met = True
                    for req_key, req_value in chapter.get("requirements", {}).items():
                        if req_key not in player_data or player_data[req_key] < req_value:
                            requirements_met = False
                            break

                    if requirements_met:
                        available_chapters.append({
                            "arc": arc_name,
                            "chapter": chapter
                        })

            return available_chapters
        except Exception as e:
            logger.error(f"Error getting available chapters: {e}")
            return []

    def get_chapter_data(self, arc_name: str, chapter_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chapter data by arc name and chapter ID.

        Args:
            arc_name: Name of the arc
            chapter_id: ID of the chapter

        Returns:
            Chapter data if found, None otherwise
        """
        try:
            if arc_name not in self.story_structure:
                return None

            for chapter in self.story_structure[arc_name]["chapters"]:
                if chapter["id"] == chapter_id:
                    return chapter

            return None
        except Exception as e:
            logger.error(f"Error getting chapter data: {e}")
            return None

    def start_story(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start or continue the story mode for a player.

        Args:
            player_data: The player's current data

        Returns:
            Dictionary containing updated player data and chapter information
        """
        try:
            # Initialize story progress if not exists
            if "story_progress" not in player_data:
                player_data["story_progress"] = {
                    "current_chapter": None,
                    "completed_chapters": [],
                    "story_choices": {},
                    "flags": {}
                }

            # Get current chapter
            current_chapter = player_data["story_progress"].get("current_chapter")
            
            # If no current chapter, start from the beginning
            if not current_chapter:
                current_chapter = "1_1_arrival"  # First chapter ID
                player_data["story_progress"]["current_chapter"] = current_chapter

            # Get chapter data
            chapter_data = self.arc_manager.get_chapter(current_chapter)
            if not chapter_data:
                return {
                    "error": f"Chapter {current_chapter} not found",
                    "player_data": player_data
                }

            # Serialize chapter data to a dictionary
            serialized_chapter = {
                "id": chapter_data.chapter_id,
                "title": chapter_data.title,
                "description": chapter_data.description,
                "type": chapter_data.type,
                "phase": chapter_data.phase,
                "scenes": chapter_data.scenes,
                "completion_exp": chapter_data.completion_exp,
                "completion_tusd": chapter_data.completion_tusd
            }

            return {
                "player_data": player_data,
                "chapter_data": serialized_chapter
            }

        except Exception as e:
            logger.error(f"Error in start_story: {e}")
            return {
                "error": str(e),
                "player_data": player_data
            } 