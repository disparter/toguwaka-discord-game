from typing import Dict, List, Any, Optional, Union
import json
import logging
from .interfaces import Chapter

logger = logging.getLogger('tokugawa_bot')

class BaseChapter(Chapter):
    """
    Base implementation of the Chapter interface.
    Provides common functionality for all chapter types.
    """
    def __init__(self, chapter_id: str, data: Dict[str, Any]):
        """
        Initialize a chapter with its data.

        Args:
            chapter_id: Unique identifier for the chapter
            data: Dictionary containing chapter data
        """
        self.chapter_id = chapter_id
        self.data = data
        self.title = data.get("title", "Untitled Chapter")
        self.description = data.get("description", "No description available.")
        self.dialogues = data.get("dialogues", [])
        self.choices = data.get("choices", [])
        self.completion_exp = data.get("completion_exp", 0)
        self.completion_tusd = data.get("completion_tusd", 0)
        self.next_chapter = data.get("next_chapter")

    def get_title(self) -> str:
        """Returns the chapter title."""
        return self.title

    def get_description(self) -> str:
        """Returns the chapter description."""
        return self.description

    def start(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts the chapter for a player.
        Returns data needed to present the chapter to the player.
        """
        # Initialize chapter state if not already present
        story_progress = player_data.get("story_progress", {})
        if not story_progress:
            story_progress = {
                "current_year": 1,
                "current_chapter": 1,
                "current_challenge_chapter": None,
                "completed_chapters": [],
                "completed_challenge_chapters": [],
                "club_progress": {},
                "villain_defeats": [],
                "minion_defeats": [],
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "story_choices": {}
            }

        # Set current chapter
        # Handle chapter IDs with multiple underscores (e.g., 1_1_2)
        parts = self.chapter_id.split("_")
        if len(parts) >= 2:
            story_progress["current_year"] = int(parts[0])
            story_progress["current_chapter"] = int(parts[1])
        else:
            story_progress["current_year"] = 1
            story_progress["current_chapter"] = 1

        # Set current dialogue index to 0
        story_progress["current_dialogue_index"] = 0

        # Update player data
        player_data["story_progress"] = story_progress

        return {
            "player_data": player_data,
            "chapter_data": {
                "id": self.chapter_id,
                "title": self.title,
                "description": self.description,
                "current_dialogue": self.dialogues[0] if self.dialogues else None
            }
        }

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Processes a player's choice and returns the next state.
        """
        story_progress = player_data.get("story_progress", {})
        current_dialogue_index = story_progress.get("current_dialogue_index", 0)

        # Get current dialogue
        if current_dialogue_index < len(self.dialogues):
            current_dialogue = self.dialogues[current_dialogue_index]
        else:
            # If we're past the dialogues, we're in the choice phase
            current_dialogue = {"choices": self.choices}

        # Check if the current dialogue has choices
        if "choices" in current_dialogue and choice_index < len(current_dialogue["choices"]):
            choice = current_dialogue["choices"][choice_index]

            # Record the choice
            chapter_choices = story_progress.get("story_choices", {}).get(self.chapter_id, {})
            choice_key = f"dialogue_{current_dialogue_index}_choice"
            chapter_choices[choice_key] = choice_index

            if "story_choices" not in story_progress:
                story_progress["story_choices"] = {}
            story_progress["story_choices"][self.chapter_id] = chapter_choices

            # Process affinity changes if present
            if "affinity_change" in choice:
                character_relationships = story_progress.get("character_relationships", {})
                for character, change in choice["affinity_change"].items():
                    current_affinity = character_relationships.get(character, 0)
                    character_relationships[character] = current_affinity + change
                story_progress["character_relationships"] = character_relationships

            # Move to the next dialogue if specified
            if "next_dialogue" in choice:
                story_progress["current_dialogue_index"] = choice["next_dialogue"]
            else:
                # Otherwise, just move to the next dialogue
                story_progress["current_dialogue_index"] = current_dialogue_index + 1
        else:
            # If there are no choices, just move to the next dialogue
            story_progress["current_dialogue_index"] = current_dialogue_index + 1

        # Update player data
        player_data["story_progress"] = story_progress

        # Get the next dialogue
        next_dialogue_index = story_progress["current_dialogue_index"]
        next_dialogue = None

        if next_dialogue_index < len(self.dialogues):
            next_dialogue = self.dialogues[next_dialogue_index]

        return {
            "player_data": player_data,
            "chapter_data": {
                "id": self.chapter_id,
                "title": self.title,
                "description": self.description,
                "current_dialogue": next_dialogue,
                "choices": self.choices if next_dialogue is None else next_dialogue.get("choices", [])
            }
        }

    def complete(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completes the chapter and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})

        # Add chapter to completed chapters
        completed_chapters = story_progress.get("completed_chapters", [])
        if self.chapter_id not in completed_chapters:
            completed_chapters.append(self.chapter_id)
        story_progress["completed_chapters"] = completed_chapters

        # Award completion rewards
        player_data["exp"] = player_data.get("exp", 0) + self.completion_exp
        player_data["tusd"] = player_data.get("tusd", 0) + self.completion_tusd

        # Update player data
        player_data["story_progress"] = story_progress

        return player_data

    def get_next_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the ID of the next chapter based on player choices and state.
        """
        # By default, return the next chapter specified in the data
        if self.next_chapter:
            # Handle chapter IDs with multiple underscores (e.g., 1_1_2)
            parts = self.chapter_id.split("_")
            year = parts[0] if len(parts) >= 1 else "1"

            # Check if next_chapter already contains year information
            if "_" in self.next_chapter:
                return self.next_chapter
            else:
                return f"{year}_{self.next_chapter}"
        return None


class StoryChapter(BaseChapter):
    """
    Implementation of a standard story chapter.
    """
    def __init__(self, chapter_id: str, data: Dict[str, Any]):
        super().__init__(chapter_id, data)

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Processes a player's choice in a story chapter.
        May have special handling for story-specific choices.
        """
        result = super().process_choice(player_data, choice_index)

        # Additional story-specific processing can be added here

        return result


class ChallengeChapter(BaseChapter):
    """
    Implementation of a challenge chapter with special mechanics.
    """
    def __init__(self, chapter_id: str, data: Dict[str, Any]):
        super().__init__(chapter_id, data)
        self.challenge_type = data.get("challenge_type", "generic")
        self.difficulty = data.get("difficulty", 1)
        self.rewards = data.get("rewards", {})

    def start(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts the challenge chapter for a player.
        """
        result = super().start(player_data)

        # Set current challenge chapter
        story_progress = result["player_data"]["story_progress"]
        story_progress["current_challenge_chapter"] = self.chapter_id
        result["player_data"]["story_progress"] = story_progress

        # Add challenge-specific data
        result["chapter_data"]["challenge_type"] = self.challenge_type
        result["chapter_data"]["difficulty"] = self.difficulty

        return result

    def complete(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completes the challenge chapter and awards special rewards.
        """
        player_data = super().complete(player_data)

        # Add to completed challenge chapters
        story_progress = player_data["story_progress"]
        completed_challenge_chapters = story_progress.get("completed_challenge_chapters", [])
        if self.chapter_id not in completed_challenge_chapters:
            completed_challenge_chapters.append(self.chapter_id)
        story_progress["completed_challenge_chapters"] = completed_challenge_chapters

        # Clear current challenge chapter
        story_progress["current_challenge_chapter"] = None

        # Award special rewards
        for reward_type, reward_value in self.rewards.items():
            if reward_type == "exp":
                player_data["exp"] = player_data.get("exp", 0) + reward_value
            elif reward_type == "tusd":
                player_data["tusd"] = player_data.get("tusd", 0) + reward_value
            elif reward_type == "hierarchy_points":
                story_progress["hierarchy_points"] = story_progress.get("hierarchy_points", 0) + reward_value
            elif reward_type == "special_item":
                special_items = story_progress.get("special_items", [])
                if reward_value not in special_items:
                    special_items.append(reward_value)
                story_progress["special_items"] = special_items

        # Update player data
        player_data["story_progress"] = story_progress

        return player_data


class BranchingChapter(BaseChapter):
    """
    Implementation of a chapter with multiple branching paths.
    """
    def __init__(self, chapter_id: str, data: Dict[str, Any]):
        super().__init__(chapter_id, data)
        self.branches = data.get("branches", {})

    def get_next_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the next chapter based on the player's choices.
        """
        story_progress = player_data.get("story_progress", {})
        chapter_choices = story_progress.get("story_choices", {}).get(self.chapter_id, {})

        # Check if any branch conditions are met
        for branch_id, branch_data in self.branches.items():
            conditions = branch_data.get("conditions", {})
            conditions_met = True

            for condition_key, condition_value in conditions.items():
                if condition_key.startswith("choice_"):
                    # Check choice condition
                    choice_index = int(condition_key.split("_")[1])
                    if chapter_choices.get(f"dialogue_{choice_index}_choice") != condition_value:
                        conditions_met = False
                        break
                elif condition_key == "attribute":
                    # Check attribute condition
                    attribute = condition_value.get("name")
                    threshold = condition_value.get("threshold", 0)
                    if player_data.get(attribute, 0) < threshold:
                        conditions_met = False
                        break
                elif condition_key == "affinity":
                    # Check affinity condition
                    character = condition_value.get("character")
                    threshold = condition_value.get("threshold", 0)
                    character_relationships = story_progress.get("character_relationships", {})
                    if character_relationships.get(character, 0) < threshold:
                        conditions_met = False
                        break

            if conditions_met:
                return branch_data.get("next_chapter")

        # If no branch conditions are met, use the default next chapter
        return super().get_next_chapter(player_data)
