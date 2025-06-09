from typing import Dict, List, Any, Optional, Union
import json
import logging
from .interfaces import Chapter
import re

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
        self._parse_chapter_id()

    def _parse_chapter_id(self) -> None:
        """Parse the chapter ID to extract base ID and suffix."""
        # Match pattern like "chapter_1_a" or "chapter_1"
        match = re.match(r"(.+?)(?:_([a-z]))?$", self.chapter_id)
        if match:
            self.base_id = match.group(1)
            self.suffix = match.group(2) if match.group(2) else None
        else:
            self.base_id = self.chapter_id
            self.suffix = None

    def get_id(self) -> str:
        """Get the full chapter ID."""
        return self.chapter_id

    def get_base_id(self) -> str:
        """Get the base chapter ID without suffix."""
        return self.base_id

    def get_suffix(self) -> Optional[str]:
        """Get the chapter suffix if it exists."""
        return self.suffix

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

        # Debug log for choices
        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - choices: {self.choices}")

        # Get current dialogue choices if available
        current_dialogue_choices = []
        if self.dialogues and len(self.dialogues) > 0:
            current_dialogue = self.dialogues[0]
            if isinstance(current_dialogue, dict) and "choices" in current_dialogue:
                current_dialogue_choices = current_dialogue.get("choices", [])
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - found dialogue-specific choices: {current_dialogue_choices}")

        # Check if we need to use choices from additional_dialogues for the first dialogue
        elif hasattr(self, 'data') and 'additional_dialogues' in self.data:
            # First dialogue is at index 0
            if '0' in self.data['additional_dialogues']:
                additional_dialogue = self.data['additional_dialogues']['0']
                # Check if the last item in additional_dialogue contains choices
                if isinstance(additional_dialogue[-1], dict) and "choices" in additional_dialogue[-1]:
                    current_dialogue_choices = additional_dialogue[-1].get("choices", [])
                    logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - found choices in additional_dialogues: {current_dialogue_choices}")

        # Use dialogue-specific choices if available, otherwise use chapter-level choices
        if current_dialogue_choices:
            choices_to_display = current_dialogue_choices
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - using dialogue-specific choices")
        else:
            # Check if there are choices_1, choices_2, etc. for the first dialogue
            choice_key = "choices_1"  # For the first set of choices
            if hasattr(self, 'data') and choice_key in self.data:
                choices_to_display = self.data[choice_key]
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - found indexed choices: {choices_to_display}")
            else:
                # If no specific choices found, use chapter-level choices
                choices_to_display = self.choices
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - using chapter-level choices")

        # Fallback message if no choices are available
        if not choices_to_display:
            logger.warning(f"No choices available for chapter {self.chapter_id}")
            choices_to_display = [{"text": "Nenhuma escolha está disponível neste momento. Continue...", "fallback": True}]

        return {
            "player_data": player_data,
            "chapter_data": {
                "id": self.chapter_id,
                "title": self.title,
                "description": self.description,
                "current_dialogue": self.dialogues[0] if self.dialogues else None,
                "choices": choices_to_display
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
            # If we're past the dialogues, check if there are indexed choices for this index
            choice_key = f"choices_{current_dialogue_index}"
            if hasattr(self, 'data') and choice_key in self.data:
                current_dialogue = {"choices": self.data[choice_key]}
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - using indexed choices for dialogue {current_dialogue_index}")
            else:
                # If no indexed choices, use chapter-level choices
                current_dialogue = {"choices": self.choices}
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - using chapter-level choices for dialogue {current_dialogue_index}")

        # Debug log for current dialogue and choices
        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - current_dialogue_index: {current_dialogue_index}")
        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - current_dialogue: {current_dialogue}")

        dialogue_choices = current_dialogue.get("choices", [])
        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - dialogue_choices: {dialogue_choices}")
        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - choice_index: {choice_index}")

        # Check if the current dialogue has choices
        if "choices" in current_dialogue and choice_index < len(current_dialogue["choices"]):
            choice = current_dialogue["choices"][choice_index]
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - selected choice: {choice}")

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

            # Handle attribute checks if present
            if "attribute_check" in choice:
                attribute = choice["attribute_check"]
                threshold = choice.get("threshold", 0)
                player_attribute_value = player_data.get(attribute, 0)

                # Check if player meets the threshold
                check_passed = player_attribute_value >= threshold
                logger.info(f"Attribute check for {attribute}: player value {player_attribute_value}, threshold {threshold}, passed: {check_passed}")

                # Set challenge result for conditional next chapter
                if "challenge_result" not in story_progress:
                    story_progress["challenge_result"] = {}

                if check_passed:
                    story_progress["challenge_result"] = {"result": "success"}
                else:
                    story_progress["challenge_result"] = {"result": "failure"}

                # Store the next dialogue index based on attribute check result
                next_dialogue = choice.get("next_dialogue")
                if next_dialogue is not None:
                    # If we have additional_dialogues with success/failure placeholders
                    if hasattr(self, 'data') and 'additional_dialogues' in self.data:
                        next_dialogue_str = str(next_dialogue)
                        if next_dialogue_str in self.data['additional_dialogues']:
                            additional_dialogue = self.data['additional_dialogues'][next_dialogue_str]

                            # Check if there are success/failure placeholders
                            for i, dialogue_item in enumerate(additional_dialogue):
                                if isinstance(dialogue_item, dict) and "text" in dialogue_item:
                                    if dialogue_item["text"] == "SUCCESS_PLACEHOLDER":
                                        # Replace with success dialogue
                                        success_key = f"success_{next_dialogue}"
                                        if success_key in self.data['additional_dialogues']:
                                            # Use the success dialogue
                                            if check_passed:
                                                additional_dialogue[i] = {"npc": dialogue_item.get("npc", "Narrador"), "text": self.data['additional_dialogues'][success_key][0]["text"]}
                                            else:
                                                # If check failed, use the failure dialogue
                                                failure_key = f"failure_{next_dialogue}"
                                                if failure_key in self.data['additional_dialogues']:
                                                    additional_dialogue[i] = {"npc": dialogue_item.get("npc", "Narrador"), "text": self.data['additional_dialogues'][failure_key][0]["text"]}

                                    elif dialogue_item["text"] == "FAILURE_PLACEHOLDER":
                                        # Replace with failure dialogue
                                        failure_key = f"failure_{next_dialogue}"
                                        if failure_key in self.data['additional_dialogues']:
                                            # Use the failure dialogue
                                            if not check_passed:
                                                additional_dialogue[i] = {"npc": dialogue_item.get("npc", "Narrador"), "text": self.data['additional_dialogues'][failure_key][0]["text"]}
                                            else:
                                                # If check passed, use the success dialogue
                                                success_key = f"success_{next_dialogue}"
                                                if success_key in self.data['additional_dialogues']:
                                                    additional_dialogue[i] = {"npc": dialogue_item.get("npc", "Narrador"), "text": self.data['additional_dialogues'][success_key][0]["text"]}

                    story_progress["current_dialogue_index"] = next_dialogue
                    logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - moving to specified dialogue after attribute check: {next_dialogue}")
                else:
                    # If no next_dialogue specified, move to the next dialogue
                    story_progress["current_dialogue_index"] = current_dialogue_index + 1
                    logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - moving to next dialogue after attribute check: {current_dialogue_index + 1}")

            # If no attribute check, just move to the next dialogue if specified
            elif "next_dialogue" in choice:
                story_progress["current_dialogue_index"] = choice["next_dialogue"]
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - moving to specified dialogue: {choice['next_dialogue']}")
            else:
                # Otherwise, just move to the next dialogue
                story_progress["current_dialogue_index"] = current_dialogue_index + 1
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - moving to next dialogue: {current_dialogue_index + 1}")
        else:
            # Check if this is a special case for club-specific dialogues
            if hasattr(self, 'data') and (
                'club_dialogues' in self.data or 
                'club_specific_dialogues' in self.data
            ):
                # This is likely a chapter with club-specific dialogues
                # Instead of warning, we'll handle this as a special case
                # Just move to the next dialogue index
                story_progress["current_dialogue_index"] = current_dialogue_index + 1
                logger.info(f"Moving to next dialogue in chapter {self.chapter_id} with club-specific content")
            else:
                # If there are no choices and no special case, just move to the next dialogue
                logger.warning(f"No valid choice found for index {choice_index} in chapter {self.chapter_id}, dialogue {current_dialogue_index}")
                story_progress["current_dialogue_index"] = current_dialogue_index + 1

        # Update player data
        player_data["story_progress"] = story_progress

        # Get the next dialogue
        next_dialogue_index = story_progress["current_dialogue_index"]
        next_dialogue = None

        if next_dialogue_index < len(self.dialogues):
            next_dialogue = self.dialogues[next_dialogue_index]
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - next_dialogue: {next_dialogue}")

        # Get next dialogue choices if available
        next_dialogue_choices = []
        if next_dialogue and isinstance(next_dialogue, dict) and "choices" in next_dialogue:
            next_dialogue_choices = next_dialogue.get("choices", [])
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - found dialogue-specific choices: {next_dialogue_choices}")

        # Check if we need to use choices from additional_dialogues
        elif hasattr(self, 'data') and 'additional_dialogues' in self.data:
            # Convert next_dialogue_index to string for lookup in additional_dialogues
            next_dialogue_index_str = str(next_dialogue_index)
            if next_dialogue_index_str in self.data['additional_dialogues']:
                additional_dialogue = self.data['additional_dialogues'][next_dialogue_index_str]
                # Check if the last item in additional_dialogue contains choices
                if isinstance(additional_dialogue[-1], dict) and "choices" in additional_dialogue[-1]:
                    next_dialogue_choices = additional_dialogue[-1].get("choices", [])
                    logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - found choices in additional_dialogues: {next_dialogue_choices}")

        # Check if there are indexed choices for this dialogue
        choice_key = f"choices_{next_dialogue_index}"
        if not next_dialogue_choices and hasattr(self, 'data') and choice_key in self.data:
            next_dialogue_choices = self.data[choice_key]
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - found indexed choices: {next_dialogue_choices}")

        # Check if there are shared_dialogue_choices for this dialogue
        if not next_dialogue_choices and hasattr(self, 'data') and 'shared_dialogue_choices' in self.data:
            shared_dialogue_choices = self.data.get('shared_dialogue_choices', [])
            if shared_dialogue_choices:
                next_dialogue_choices = shared_dialogue_choices
                logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - using shared_dialogue_choices")

        # Use dialogue-specific choices if available, otherwise use chapter-level choices
        # But only use chapter-level choices if we're at the beginning or if explicitly needed
        if next_dialogue_choices:
            choices_to_display = next_dialogue_choices
        elif next_dialogue_index == 0:  # Only use chapter-level choices at the beginning
            choices_to_display = self.choices
        else:
            # If no specific choices found, use chapter-level choices as fallback
            choices_to_display = self.choices
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - using fallback chapter-level choices")

        # Fallback message if no choices are available
        if not choices_to_display and next_dialogue is not None:
            logger.warning(f"No choices available for next dialogue in chapter {self.chapter_id}")
            choices_to_display = [{"text": "Nenhuma escolha está disponível neste momento. Continue...", "fallback": True}]

        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - choices_to_display: {choices_to_display}")

        # Check if we need to include shared dialogue after the current dialogue
        shared_dialogue = None
        if hasattr(self, 'data') and 'shared_dialogue' in self.data:
            shared_dialogue = self.data.get('shared_dialogue', [])
            logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} process_choice() - including shared_dialogue")

        return {
            "player_data": player_data,
            "chapter_data": {
                "id": self.chapter_id,
                "title": self.title,
                "description": self.description,
                "current_dialogue": next_dialogue,
                "shared_dialogue": shared_dialogue,
                "choices": choices_to_display
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
        # Check for conditional next chapter based on player data
        if hasattr(self, 'data') and 'conditional_next_chapter' in self.data:
            conditional_next = self.data.get('conditional_next_chapter', {})

            # Check for challenge_result based conditions
            if 'challenge_result' in conditional_next:
                challenge_conditions = conditional_next['challenge_result']
                story_progress = player_data.get("story_progress", {})
                challenge_result = story_progress.get("challenge_result", {}).get("result")

                logger.info(f"Checking challenge_result condition: player result is {challenge_result}")

                if challenge_result is not None:
                    # Check if there's a specific condition for this result
                    if challenge_result in challenge_conditions:
                        next_chapter = challenge_conditions[challenge_result]
                        logger.info(f"Using conditional next chapter for challenge_result {challenge_result}: {next_chapter}")

                        # Handle chapter IDs with multiple underscores
                        if "_" in next_chapter:
                            return next_chapter
                        else:
                            parts = self.chapter_id.split("_")
                            year = parts[0] if len(parts) >= 1 else "1"
                            return f"{year}_{next_chapter}"

                # Use default if specified and no specific condition matched
                if 'default' in challenge_conditions:
                    next_chapter = challenge_conditions['default']
                    logger.info(f"Using default conditional next chapter for challenge: {next_chapter}")

                    # Handle chapter IDs with multiple underscores
                    if "_" in next_chapter:
                        return next_chapter
                    else:
                        parts = self.chapter_id.split("_")
                        year = parts[0] if len(parts) >= 1 else "1"
                        return f"{year}_{next_chapter}"

            # Check for club_id based conditions
            if 'club_id' in conditional_next:
                club_conditions = conditional_next['club_id']
                player_club_id = player_data.get('club_id')

                if player_club_id is not None:
                    # Convert to string for comparison since JSON keys are strings
                    club_id_str = str(player_club_id)
                    if club_id_str in club_conditions:
                        next_chapter = club_conditions[club_id_str]
                        logger.info(f"Using conditional next chapter for club_id {player_club_id}: {next_chapter}")

                        # Handle chapter IDs with multiple underscores
                        if "_" in next_chapter:
                            return next_chapter
                        else:
                            parts = self.chapter_id.split("_")
                            year = parts[0] if len(parts) >= 1 else "1"
                            return f"{year}_{next_chapter}"

                # Use default if specified and no specific condition matched
                if 'default' in club_conditions:
                    next_chapter = club_conditions['default']
                    logger.info(f"Using default conditional next chapter: {next_chapter}")

                    # Handle chapter IDs with multiple underscores
                    if "_" in next_chapter:
                        return next_chapter
                    else:
                        parts = self.chapter_id.split("_")
                        year = parts[0] if len(parts) >= 1 else "1"
                        return f"{year}_{next_chapter}"

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
        self.failure_consequences = data.get("failure_consequences", {})
        self.secret_chapter = data.get("secret_chapter")

    def start(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts the challenge chapter for a player.
        """
        result = super().start(player_data)

        # Check if this challenge has already been completed
        story_progress = result["player_data"]["story_progress"]
        completed_challenge_chapters = story_progress.get("completed_challenge_chapters", [])
        failed_challenge_chapters = story_progress.get("failed_challenge_chapters", [])

        if self.chapter_id in completed_challenge_chapters:
            # Challenge already completed, add a flag to indicate this
            result["chapter_data"]["already_completed"] = True
            logger.info(f"Challenge {self.chapter_id} already completed by player {player_data.get('user_id')}")
        elif self.chapter_id in failed_challenge_chapters:
            # Challenge already failed, add a flag to indicate this
            result["chapter_data"]["already_failed"] = True
            logger.info(f"Challenge {self.chapter_id} already failed by player {player_data.get('user_id')}")
        else:
            # Set current challenge chapter
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
            elif reward_type == "unlock_chapter":
                # Unlock a special chapter
                available_chapters = story_progress.get("available_chapters", [])
                if reward_value not in available_chapters:
                    available_chapters.append(reward_value)
                story_progress["available_chapters"] = available_chapters

        # Update player data
        player_data["story_progress"] = story_progress

        return player_data

    def fail(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles the failure of a challenge and applies consequences.
        """
        # Add to failed challenge chapters
        story_progress = player_data.get("story_progress", {})
        failed_challenge_chapters = story_progress.get("failed_challenge_chapters", [])
        if self.chapter_id not in failed_challenge_chapters:
            failed_challenge_chapters.append(self.chapter_id)
        story_progress["failed_challenge_chapters"] = failed_challenge_chapters

        # Clear current challenge chapter
        story_progress["current_challenge_chapter"] = None

        # Apply failure consequences
        for consequence_type, consequence_value in self.failure_consequences.items():
            if consequence_type == "exp_loss":
                player_data["exp"] = max(0, player_data.get("exp", 0) - consequence_value)
            elif consequence_type == "tusd_loss":
                player_data["tusd"] = max(0, player_data.get("tusd", 0) - consequence_value)
            elif consequence_type == "hierarchy_points_loss":
                story_progress["hierarchy_points"] = max(0, story_progress.get("hierarchy_points", 0) - consequence_value)
            elif consequence_type == "block_chapter_arc":
                # Block future chapters in this arc
                blocked_chapter_arcs = story_progress.get("blocked_chapter_arcs", [])
                if consequence_value not in blocked_chapter_arcs:
                    blocked_chapter_arcs.append(consequence_value)
                story_progress["blocked_chapter_arcs"] = blocked_chapter_arcs
            elif consequence_type == "unlock_secret_chapter":
                # Unlock a secret chapter (alternative path)
                available_chapters = story_progress.get("available_chapters", [])
                if consequence_value not in available_chapters:
                    available_chapters.append(consequence_value)
                story_progress["available_chapters"] = available_chapters

        # Update player data
        player_data["story_progress"] = story_progress

        logger.info(f"Challenge {self.chapter_id} failed by player {player_data.get('user_id')}")

        return player_data


class BranchingChapter(BaseChapter):
    """
    Implementation of a chapter with multiple branching paths.
    """
    def __init__(self, chapter_id: str, data: Dict[str, Any]):
        super().__init__(chapter_id, data)
        self.branches = data.get("branches", {})
        # For branching chapters with scenes structure (like mystery_chapter.json)
        self.scenes = data.get("scenes", [])

    def start(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts the branching chapter for a player.
        For chapters with a scenes structure, handles the first scene.
        """
        # Check if this is a scene-based chapter
        if self.scenes:
            logger.debug(f"[DEBUG_LOG] Starting scene-based branching chapter: {self.chapter_id}")
            # Initialize chapter state
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

            # Set current scene to the first scene
            story_progress["current_scene"] = self.scenes[0]["scene_id"] if self.scenes else None
            story_progress["current_dialogue_index"] = 0

            # Update player data
            player_data["story_progress"] = story_progress

            # Get the first scene
            first_scene = self.scenes[0] if self.scenes else None

            if first_scene:
                logger.debug(f"[DEBUG_LOG] First scene: {first_scene['scene_id']}")
                # Get choices from the first scene
                choices_to_display = first_scene.get("choices", [])
                logger.debug(f"[DEBUG_LOG] First scene choices: {choices_to_display}")

                # Fallback message if no choices are available
                if not choices_to_display:
                    logger.warning(f"No choices available for first scene in chapter {self.chapter_id}")
                    choices_to_display = [{"text": "Nenhuma escolha está disponível neste momento. Continue...", "fallback": True}]

                return {
                    "player_data": player_data,
                    "chapter_data": {
                        "id": self.chapter_id,
                        "title": first_scene.get("title", self.title),
                        "description": first_scene.get("description", self.description),
                        "current_dialogue": first_scene.get("dialogue", []),
                        "choices": choices_to_display
                    }
                }

        # If not a scene-based chapter or no scenes found, fall back to standard behavior
        return super().start(player_data)

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Processes a player's choice in a branching chapter.
        For scene-based chapters, handles scene transitions.
        """
        # Check if this is a scene-based chapter
        if self.scenes:
            story_progress = player_data.get("story_progress", {})
            current_scene_id = story_progress.get("current_scene")

            # Find the current scene
            current_scene = None
            for scene in self.scenes:
                if scene["scene_id"] == current_scene_id:
                    current_scene = scene
                    break

            if current_scene and "choices" in current_scene and choice_index < len(current_scene["choices"]):
                choice = current_scene["choices"][choice_index]
                logger.debug(f"[DEBUG_LOG] Selected choice in scene {current_scene_id}: {choice}")

                # Record the choice
                chapter_choices = story_progress.get("story_choices", {}).get(self.chapter_id, {})
                choice_key = f"scene_{current_scene_id}_choice"
                chapter_choices[choice_key] = choice_index

                if "story_choices" not in story_progress:
                    story_progress["story_choices"] = {}
                story_progress["story_choices"][self.chapter_id] = chapter_choices

                # Process rewards if present
                if "rewards" in choice:
                    for reward_type, reward_value in choice["rewards"].items():
                        if reward_type == "exp":
                            player_data["exp"] = player_data.get("exp", 0) + reward_value
                        elif reward_type == "tusd":
                            player_data["tusd"] = player_data.get("tusd", 0) + reward_value
                        elif reward_type in player_data:
                            player_data[reward_type] = player_data.get(reward_type, 0) + reward_value

                # Move to the next scene if specified
                next_scene_id = choice.get("next_scene")
                if next_scene_id:
                    story_progress["current_scene"] = next_scene_id

                    # Find the next scene
                    next_scene = None
                    for scene in self.scenes:
                        if scene["scene_id"] == next_scene_id:
                            next_scene = scene
                            break

                    if next_scene:
                        # Update player data
                        player_data["story_progress"] = story_progress

                        # Get choices from the next scene
                        choices_to_display = next_scene.get("choices", [])

                        # Fallback message if no choices are available
                        if not choices_to_display:
                            logger.warning(f"No choices available for scene {next_scene_id} in chapter {self.chapter_id}")
                            choices_to_display = [{"text": "Nenhuma escolha está disponível neste momento. Continue...", "fallback": True}]

                        return {
                            "player_data": player_data,
                            "chapter_data": {
                                "id": self.chapter_id,
                                "title": next_scene.get("title", self.title),
                                "description": next_scene.get("description", self.description),
                                "current_dialogue": next_scene.get("dialogue", []),
                                "choices": choices_to_display
                            }
                        }

            # If we couldn't process the choice or find the next scene, log an error
            logger.warning(f"Could not process choice {choice_index} in scene {current_scene_id} of chapter {self.chapter_id}")

        # If not a scene-based chapter or couldn't process the scene choice, fall back to standard behavior
        return super().process_choice(player_data, choice_index)

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

    def get_content(self, club: Optional[str] = None) -> str:
        """
        Get the chapter content, with club-specific content if available.
        
        Args:
            club: The player's club affiliation
            
        Returns:
            The appropriate content string
        """
        if club and "club_specific_content" in self.data:
            return self.data["club_specific_content"].get(club, self.data["club_specific_content"].get("default", self.data.get("content", "")))
        return self.data.get("content", "")

    def get_choices(self, player_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get available choices for the chapter, filtered by conditions if any.
        
        Args:
            player_data: Player data to check conditions against
            
        Returns:
            List of available choices
        """
        choices = self.data.get("choices", [])
        if not player_data:
            return choices

        available_choices = []
        for choice in choices:
            if "condition" in choice:
                if self._check_condition(choice["condition"], player_data):
                    available_choices.append(choice)
            else:
                available_choices.append(choice)
        return available_choices

    def _check_condition(self, condition: Dict[str, Any], player_data: Dict[str, Any]) -> bool:
        """
        Check if a condition is met based on player data.
        
        Args:
            condition: The condition to check
            player_data: Player data to check against
            
        Returns:
            True if condition is met, False otherwise
        """
        if "stat" in condition:
            stat = condition["stat"]
            value = condition["value"]
            operator = condition.get("operator", ">=")
            
            player_stat = player_data.get("attributes", {}).get(stat, 0)
            
            if operator == ">=":
                return player_stat >= value
            elif operator == ">":
                return player_stat > value
            elif operator == "<=":
                return player_stat <= value
            elif operator == "<":
                return player_stat < value
            elif operator == "==":
                return player_stat == value
            elif operator == "!=":
                return player_stat != value
                
        return True

    def get_requirements(self) -> Dict[str, Any]:
        """Get chapter requirements."""
        return self.data.get("requirements", {})

    def get_challenge_id(self) -> Optional[str]:
        """Get the challenge ID if this is a challenge chapter."""
        return self.data.get("challenge_id")

    def get_club_specific_content(self) -> Dict[str, str]:
        """Get all club-specific content."""
        return self.data.get("club_specific_content", {})
