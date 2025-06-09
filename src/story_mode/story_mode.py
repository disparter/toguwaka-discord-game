"""
Story Mode module for Academia Tokugawa.

This module handles the story structure, chapter management, and narrative progression.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

class StoryMode:
    """
    Class for managing the story mode, including story structure and chapters.
    """
    
    def __init__(self, data_dir: str = "data/story_mode"):
        """
        Initialize the story mode.
        
        Args:
            data_dir: Path to the directory containing story data
        """
        self.data_dir = Path(data_dir)
        self.arcs_dir = self.data_dir / "arcs"
        self.chapters_dir = self.data_dir / "chapters"
        self.story_structure = {}
        
        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.arcs_dir.mkdir(parents=True, exist_ok=True)
        self.chapters_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize story structure
        self._load_story_structure()
        
        logger.info("StoryMode initialized")

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