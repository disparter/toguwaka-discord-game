from typing import Dict, List, Any, Optional, Union
import json
import logging
from .interfaces import Chapter
import re

logger = logging.getLogger('tokugawa_bot')

class BaseChapter(Chapter):
    """
    Base class for all chapter types.
    """

    def __init__(self, chapter_id: str, chapter_data: Dict[str, Any]):
        """
        Initialize a base chapter.

        Args:
            chapter_id: The chapter's unique identifier
            chapter_data: The chapter's data dictionary
        """
        self.chapter_id = chapter_id
        self.title = chapter_data.get("title", "")
        self.description = chapter_data.get("description", "")
        self.type = chapter_data.get("type", "story")
        self.phase = chapter_data.get("phase", "")
        self.completion_exp = chapter_data.get("completion_exp", 0)
        self.completion_tusd = chapter_data.get("completion_tusd", 0)
        self.dialogues = chapter_data.get("dialogues", [])
        self.choices = chapter_data.get("choices", [])
        self.next_chapter = chapter_data.get("next_chapter")
        self._parse_chapter_id()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the chapter to a dictionary for serialization.

        Returns:
            Dictionary representation of the chapter
        """
        return {
            "id": self.chapter_id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "phase": self.phase,
            "completion_exp": self.completion_exp,
            "completion_tusd": self.completion_tusd
        }

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Process a player's choice and return updated player data and chapter information.

        Args:
            player_data: The player's current data
            choice_index: The index of the chosen option

        Returns:
            Dictionary containing updated player data and chapter information
        """
        raise NotImplementedError("Subclasses must implement process_choice")

    def complete(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete the chapter and return updated player data.

        Args:
            player_data: The player's current data

        Returns:
            Updated player data
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

    def get_available_choices(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get the list of available choices for the current state.
        
        Args:
            player_data: Current player data
            
        Returns:
            List of available choices
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
            else:
                # If no indexed choices, use chapter-level choices
                current_dialogue = {"choices": self.choices}

        # Get choices from current dialogue
        dialogue_choices = current_dialogue.get("choices", [])

        # Filter choices based on requirements
        available_choices = []
        for choice in dialogue_choices:
            if "requirements" in choice:
                # Check if player meets all requirements
                requirements = choice["requirements"]
                meets_requirements = True
                for stat, value in requirements.items():
                    if player_data.get(stat, 0) < value:
                        meets_requirements = False
                        break
                if meets_requirements:
                    available_choices.append(choice)
            else:
                available_choices.append(choice)

        return available_choices

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
                "current_chapter": "1_1",  # Enforce string chapter ID
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

        # Set current chapter as string
        story_progress["current_chapter"] = str(self.chapter_id)
        logger.debug(f"[DEBUG_LOG] Setting current_chapter to {story_progress['current_chapter']} (type: {type(story_progress['current_chapter'])})")

        # Handle chapter IDs with multiple underscores (e.g., 1_1_2)
        parts = self.chapter_id.split("_")
        if len(parts) >= 2:
            try:
                story_progress["current_year"] = int(parts[0])
                story_progress["current_chapter_number"] = int(parts[1])
            except Exception as e:
                logger.warning(f"[DEBUG_LOG] Could not parse year/chapter_number from chapter_id {self.chapter_id}: {e}")
        else:
            story_progress["current_year"] = 1
            story_progress["current_chapter_number"] = 1

        # Set current dialogue index to 0
        story_progress["current_dialogue_index"] = 0

        # Update player data
        player_data["story_progress"] = story_progress

        # Debug log for choices
        logger.debug(f"[DEBUG_LOG] Chapter {self.chapter_id} start() - choices: {self.choices}")
        logger.debug(f"[DEBUG_LOG] story_progress after start: {story_progress}")

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
    A story chapter that contains narrative content and choices.
    """

    def __init__(self, chapter_id: str, chapter_data: Dict[str, Any]):
        """
        Initialize a story chapter.

        Args:
            chapter_id: The chapter's unique identifier
            chapter_data: The chapter's data dictionary
        """
        super().__init__(chapter_id, chapter_data)
        self.scenes = chapter_data.get("scenes", [])
        self.current_scene_index = 0
        self.current_dialogue_index = 0
        self.shared_dialogue = []
        self.choices = []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the chapter to a dictionary for serialization.

        Returns:
            Dictionary representation of the chapter
        """
        return {
            "id": self.chapter_id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "phase": self.phase,
            "scenes": self.scenes,
            "completion_exp": self.completion_exp,
            "completion_tusd": self.completion_tusd,
            "current_scene_index": self.current_scene_index,
            "current_dialogue_index": self.current_dialogue_index,
            "shared_dialogue": self.shared_dialogue,
            "choices": self.choices
        }

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Process a player's choice and return updated player data and chapter information.

        Args:
            player_data: The player's current data
            choice_index: The index of the chosen option

        Returns:
            Dictionary containing updated player data and chapter information
        """
        if not self.choices or choice_index >= len(self.choices):
            return {
                "error": "Invalid choice",
                "player_data": player_data
            }

        choice = self.choices[choice_index]
        next_scene = choice.get("next_scene")

        # Apply choice effects
        effects = choice.get("effects", {})
        for effect_type, effect_value in effects.items():
            if effect_type == "reputation":
                for npc_id, value in effect_value.items():
                    player_data = self._update_reputation(player_data, npc_id, value)
            elif effect_type == "elemental_affinity":
                player_data = self._update_elemental_affinity(player_data, effect_value)
            elif effect_type == "knowledge":
                player_data = self._update_knowledge(player_data, effect_value)
            elif effect_type == "club_interest":
                player_data = self._update_club_interest(player_data, effect_value)

        # Record the choice
        story_progress = player_data.get("story_progress", {})
        if "story_choices" not in story_progress:
            story_progress["story_choices"] = {}
        if self.chapter_id not in story_progress["story_choices"]:
            story_progress["story_choices"][self.chapter_id] = {}
        story_progress["story_choices"][self.chapter_id][str(choice_index)] = choice
        player_data["story_progress"] = story_progress

        # Move to next scene if specified
        if next_scene:
            self.current_scene_index = next_scene
            self.current_dialogue_index = 0
            self.shared_dialogue = []
            self.choices = []

        # Get next dialogue and choices
        next_dialogue = self._get_next_dialogue()
        choices_to_display = self._get_choices()

        return {
            "player_data": player_data,
            "chapter_data": self.to_dict()
        }

    def _get_next_dialogue(self):
        # Implementation of _get_next_dialogue method
        pass

    def _get_choices(self):
        # Implementation of _get_choices method
        pass

    def _update_reputation(self, player_data: Dict[str, Any], npc_id: str, value: int) -> Dict[str, Any]:
        # Implementation of _update_reputation method
        pass

    def _update_elemental_affinity(self, player_data: Dict[str, Any], effect_value: int) -> Dict[str, Any]:
        # Implementation of _update_elemental_affinity method
        pass

    def _update_knowledge(self, player_data: Dict[str, Any], effect_value: int) -> Dict[str, Any]:
        # Implementation of _update_knowledge method
        pass

    def _update_club_interest(self, player_data: Dict[str, Any], effect_value: int) -> Dict[str, Any]:
        # Implementation of _update_club_interest method
        pass


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
