from typing import Dict, List, Any, Optional, Union
import json
import os
import logging
import sys

logger = logging.getLogger('tokugawa_bot')

class ChapterValidator:
    """
    Validates chapter JSON files to ensure they have the required fields and structure.
    """

    @staticmethod
    def validate_chapter_file(file_path: str) -> bool:
        """
        Validates a chapter JSON file.

        Args:
            file_path: Path to the chapter JSON file

        Returns:
            True if the file is valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)

            if not isinstance(chapter_data, dict):
                logger.error(f"Invalid chapter file format: {file_path}. Expected a dictionary.")
                return False

            return ChapterValidator.validate_chapter(chapter_data, file_path)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating chapter file {file_path}: {e}")
            return False

    @staticmethod
    def validate_chapter(chapter_data: Dict[str, Any], file_path: str) -> bool:
        """
        Validates a single chapter.

        Args:
            chapter_data: Chapter data dictionary
            file_path: Path to the chapter file (for error reporting)

        Returns:
            True if the chapter is valid, False otherwise
        """
        # Get chapter ID from data
        chapter_id = chapter_data.get("id") or chapter_data.get("chapter_id")
        if not chapter_id:
            logger.error(f"Chapter in {file_path} is missing id or chapter_id")
            return False

        # Check required fields
        required_fields = ["type", "title", "description", "scenes"]
        for field in required_fields:
            if field not in chapter_data:
                logger.error(f"Chapter {chapter_id} in {file_path} is missing required field: {field}")
                return False

        # Validate scenes
        scenes = chapter_data.get("scenes", [])
        if not isinstance(scenes, list):
            logger.error(f"Chapter {chapter_id} in {file_path}: 'scenes' must be a list")
            return False

        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} must be a dictionary")
                return False

            # Check required scene fields
            scene_required_fields = ["scene_id", "title", "description"]
            for field in scene_required_fields:
                if field not in scene:
                    logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} is missing required field: {field}")
                    return False

            # Validate scene choices if present
            choices = scene.get("choices", [])
            if choices:
                if not isinstance(choices, list):
                    logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} 'choices' must be a list")
                    return False

                for j, choice in enumerate(choices):
                    if not isinstance(choice, dict):
                        logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} choice {j} must be a dictionary")
                        return False

                    if "text" not in choice:
                        logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} choice {j} is missing required field 'text'")
                        return False

            # Validate scene dialogue if present
            dialogue = scene.get("dialogue", [])
            if dialogue:
                if not isinstance(dialogue, list):
                    logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} 'dialogue' must be a list")
                    return False

                for j, dialogue_entry in enumerate(dialogue):
                    if not isinstance(dialogue_entry, dict):
                        logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} dialogue entry {j} must be a dictionary")
                        return False

                    if "speaker" not in dialogue_entry or "text" not in dialogue_entry:
                        logger.error(f"Chapter {chapter_id} in {file_path}: scene {i} dialogue entry {j} is missing required fields 'speaker' or 'text'")
                        return False

        return True

    @staticmethod
    def validate_all_chapters(chapters_dir: str) -> bool:
        """
        Validates all chapter files in a directory.

        Args:
            chapters_dir: Path to the directory containing chapter JSON files

        Returns:
            True if all files are valid, False otherwise
        """
        if not os.path.exists(chapters_dir):
            logger.error(f"Chapters directory not found: {chapters_dir}")
            return False

        all_valid = True
        for filename in os.listdir(chapters_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(chapters_dir, filename)
                logger.info(f"Validating chapter file: {file_path}")
                if not ChapterValidator.validate_chapter_file(file_path):
                    all_valid = False
                    logger.error(f"Chapter file validation failed: {file_path}")
                else:
                    logger.info(f"Chapter file validation passed: {file_path}")

        return all_valid

def validate_chapters_cli():
    """
    Command-line interface for validating chapter files.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m story_mode.chapter_validator <chapters_dir>")
        return False

    chapters_dir = sys.argv[1]
    return ChapterValidator.validate_all_chapters(chapters_dir)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run validator
    success = validate_chapters_cli()
    sys.exit(0 if success else 1)
