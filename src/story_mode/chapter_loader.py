from typing import Dict, List, Any
import json
import os
import logging
from pathlib import Path
from .interfaces import Chapter, ChapterLoader
from .chapter import StoryChapter, ChallengeChapter, BranchingChapter

logger = logging.getLogger('tokugawa_bot')

class FileChapterLoader(ChapterLoader):
    """
    Implementation of ChapterLoader that loads chapters from JSON files.
    """
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.chapters: Dict[str, Chapter] = {}
        self._load_chapters()

    def _load_chapters(self) -> None:
        """Load all chapter files from the data directory."""
        # Load main story chapters
        main_chapter_dir = self.data_dir / "narrative" / "chapters"
        if not main_chapter_dir.exists():
            logger.warning(f"Main chapter directory not found: {main_chapter_dir}")
        else:
            for filename in os.listdir(main_chapter_dir):
                if filename.endswith(".json"):
                    try:
                        chapter_id = filename.replace(".json", "")
                        with open(main_chapter_dir / filename, 'r') as f:
                            chapter_data = json.load(f)
                            chapter_data["chapter_id"] = chapter_id
                            chapter = self._create_chapter(chapter_data)
                            if chapter:
                                self.chapters[chapter_id] = chapter
                            else:
                                logger.error(f"Failed to create chapter {chapter_id}")
                    except Exception as e:
                        logger.error(f"Error loading chapter {filename}: {e}")

        # Load club chapters
        club_chapter_dir = self.data_dir / "clubs"
        if not club_chapter_dir.exists():
            logger.warning(f"Club chapter directory not found: {club_chapter_dir}")
        else:
            for club_dir in os.listdir(club_chapter_dir):
                club_path = club_chapter_dir / club_dir
                if club_path.is_dir():
                    for filename in os.listdir(club_path):
                        if filename.endswith(".json"):
                            try:
                                chapter_id = f"club_{club_dir}_{filename.replace('.json', '')}"
                                with open(club_path / filename, 'r') as f:
                                    chapter_data = json.load(f)
                                    chapter_data["chapter_id"] = chapter_id
                                    chapter = self._create_chapter(chapter_data)
                                    if chapter:
                                        self.chapters[chapter_id] = chapter
                                    else:
                                        logger.error(f"Failed to create club chapter {chapter_id}")
                            except Exception as e:
                                logger.error(f"Error loading club chapter {filename}: {e}")

    def _create_chapter(self, chapter_data: Dict[str, Any]) -> Chapter:
        """Create a chapter instance based on its type."""
        chapter_type = chapter_data.get("type", "story")
        chapter_id = chapter_data.get("chapter_id", "unknown")
        
        # Validate required fields
        required_fields = ["title", "description", "scenes"]
        missing_fields = [field for field in required_fields if field not in chapter_data]
        if missing_fields:
            logger.error(f"Chapter {chapter_id} is missing required fields: {', '.join(missing_fields)}")
            return None
        
        try:
            if chapter_type == "story":
                return StoryChapter(chapter_id, chapter_data)
            elif chapter_type == "challenge":
                return ChallengeChapter(chapter_id, chapter_data)
            elif chapter_type == "branching":
                return BranchingChapter(chapter_id, chapter_data)
            else:
                logger.warning(f"Unknown chapter type: {chapter_type}, defaulting to story")
                return StoryChapter(chapter_id, chapter_data)
        except Exception as e:
            logger.error(f"Error creating chapter {chapter_id}: {e}")
            return None

    def load_chapter(self, chapter_id: str) -> Chapter:
        """Load a chapter by its ID."""
        if chapter_id not in self.chapters:
            raise ValueError(f"Chapter not found: {chapter_id}")
        return self.chapters[chapter_id]

    def get_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """Get a list of chapter IDs available to the player."""
        available_chapters = []
        for chapter_id, chapter in self.chapters.items():
            if self._is_chapter_available(chapter, player_data):
                available_chapters.append(chapter_id)
        return available_chapters

    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any]) -> bool:
        """Check if a chapter is available to the player."""
        # Check if the chapter is already completed
        completed_chapters = player_data.get("story_progress", {}).get("completed_chapters", [])
        if chapter.get_id() in completed_chapters:
            return False

        # Check chapter requirements
        requirements = chapter.get_requirements()
        if not requirements:
            return True

        # Check if this is a new player chapter
        if requirements.get("is_new_player", False):
            return len(completed_chapters) == 0

        # Check player stats
        player_stats = player_data.get("attributes", {})
        for stat, value in requirements.get("stats", {}).items():
            if player_stats.get(stat, 0) < value:
                return False

        # Check completed chapters
        for required_chapter in requirements.get("chapters", []):
            if required_chapter not in completed_chapters:
                return False

        return True 