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
        self.images_dir = self.base_dir / "assets" / "images" / "story"

        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.arc_manager = ArcManager(str(self.data_dir))
        self.event_manager = ConcreteEventManager()
        self.npc_manager = NPCManager()
        self.image_processor = ImageProcessor(str(self.images_dir))
        self.progress_manager = DefaultStoryProgressManager()
        self.consequences_system = DynamicConsequencesSystem()
        self.power_system = PowerEvolutionSystem()
        self.seasonal_event_system = SeasonalEventSystem()
        self.companion_system = CompanionSystem()
        self.club_system = ClubSystem(self.consequences_system)
        self.club_manager = ClubContentManager(base_dir)

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
