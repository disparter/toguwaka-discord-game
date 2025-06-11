from typing import Dict, List, Any, Optional, Union, TypedDict, Callable
import json
import logging
from .interfaces import StoryProgressManager
from utils.persistence.dynamodb_story import get_story_progress, update_story_progress

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
    Default implementation of StoryProgressManager that stores progress in DynamoDB.
    """
    async def get_current_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the ID of the player's current chapter.
        """
        progress = await get_story_progress(player_data["user_id"])
        return progress.get("current_chapter")
    
    async def set_current_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Sets the player's current chapter and returns updated player data.
        """
        progress = await get_story_progress(player_data["user_id"])
        progress["current_chapter"] = chapter_id
        await update_story_progress(player_data["user_id"], progress)
        return player_data
    
    async def complete_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Marks a chapter as completed and returns updated player data.
        """
        progress = await get_story_progress(player_data["user_id"])
        completed_chapters = progress.get("completed_chapters", [])
        if chapter_id not in completed_chapters:
            completed_chapters.append(chapter_id)
            progress["completed_chapters"] = completed_chapters
            await update_story_progress(player_data["user_id"], progress)
        return player_data
    
    async def record_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_value: Any) -> Dict[str, Any]:
        """
        Records a player's choice and returns updated player data.
        """
        progress = await get_story_progress(player_data["user_id"])
        choices = progress.get("choices", {})
        chapter_choices = choices.get(chapter_id, {})
        chapter_choices[choice_key] = choice_value
        choices[chapter_id] = chapter_choices
        progress["choices"] = choices
        await update_story_progress(player_data["user_id"], progress)
        return player_data
    
    async def get_completed_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs completed by the player.
        """
        progress = await get_story_progress(player_data["user_id"])
        return progress.get("completed_chapters", [])
    
    async def get_completed_challenge_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of challenge chapter IDs completed by the player.
        """
        progress = await get_story_progress(player_data["user_id"])
        return progress.get("completed_challenge_chapters", [])
    
    async def get_story_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str) -> Optional[Any]:
        """
        Returns a player's choice for a specific chapter and key.
        """
        progress = await get_story_progress(player_data["user_id"])
        choices = progress.get("choices", {})
        chapter_choices = choices.get(chapter_id, {})
        return chapter_choices.get(choice_key)
    
    async def get_all_story_choices(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Returns all story choices made by the player.
        """
        progress = await get_story_progress(player_data["user_id"])
        return progress.get("choices", {})
    
    async def get_next_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs that are available to the player next.
        """
        progress = await get_story_progress(player_data["user_id"])
        current_chapter = progress.get("current_chapter")
        completed_chapters = progress.get("completed_chapters", [])
        
        # If no current chapter, only first chapter is available
        if not current_chapter:
            return ["chapter_1"]
        
        # Get next chapters based on current chapter
        next_chapters = []
        if current_chapter == "chapter_1":
            next_chapters = ["chapter_2", "chapter_3"]
        elif current_chapter == "chapter_2":
            next_chapters = ["chapter_4"]
        elif current_chapter == "chapter_3":
            next_chapters = ["chapter_5"]
        elif current_chapter == "chapter_4":
            next_chapters = ["chapter_6"]
        elif current_chapter == "chapter_5":
            next_chapters = ["chapter_7"]
        elif current_chapter == "chapter_6":
            next_chapters = ["chapter_8"]
        elif current_chapter == "chapter_7":
            next_chapters = ["chapter_9"]
        elif current_chapter == "chapter_8":
            next_chapters = ["chapter_10"]
        
        # Filter out completed chapters
        return [chapter for chapter in next_chapters if chapter not in completed_chapters]
    
    async def initialize_story_progress(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initializes story progress for a new player.
        """
        progress = {
            "current_chapter": None,
            "completed_chapters": [],
            "completed_challenge_chapters": [],
            "choices": {},
            "hierarchy_tier": 1,
            "hierarchy_points": 0
        }
        await update_story_progress(player_data["user_id"], progress)
        return player_data
    
    async def update_hierarchy_tier(self, player_data: Dict[str, Any], new_tier: int) -> Dict[str, Any]:
        """
        Updates the player's hierarchy tier and returns updated player data.
        """
        progress = await get_story_progress(player_data["user_id"])
        progress["hierarchy_tier"] = new_tier
        await update_story_progress(player_data["user_id"], progress)
        return player_data
    
    async def add_hierarchy_points(self, player_data: Dict[str, Any], points: int) -> Dict[str, Any]:
        """
        Adds hierarchy points to the player and updates tier if necessary.
        """
        progress = await get_story_progress(player_data["user_id"])
        current_points = progress.get("hierarchy_points", 0)
        current_tier = progress.get("hierarchy_tier", 1)
        
        new_points = current_points + points
        new_tier = current_tier
        
        # Update tier based on points
        if new_points >= 1000:
            new_tier = 4
        elif new_points >= 500:
            new_tier = 3
        elif new_points >= 100:
            new_tier = 2
        
        progress["hierarchy_points"] = new_points
        if new_tier != current_tier:
            progress["hierarchy_tier"] = new_tier
        
        await update_story_progress(player_data["user_id"], progress)
        return player_data
    
    async def save_progress(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves player progress to persistent storage.
        """
        progress = await get_story_progress(player_data["user_id"])
        await update_story_progress(player_data["user_id"], progress)
        return player_data
