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
                chapters_data = json.load(f)

            if not isinstance(chapters_data, dict):
                logger.error(f"Invalid chapter file format: {file_path}. Expected a dictionary.")
                return False

            # Check if it's a single chapter or multiple chapters
            if "chapter_id" in chapters_data:
                # Single chapter
                return ChapterValidator.validate_chapter(chapters_data, file_path)
            else:
                # Multiple chapters
                all_valid = True
                for chapter_id, chapter_data in chapters_data.items():
                    if not ChapterValidator.validate_chapter(chapter_data, file_path, chapter_id):
                        all_valid = False
                return all_valid

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating chapter file {file_path}: {e}")
            return False

    @staticmethod
    def validate_chapter(chapter_data: Dict[str, Any], file_path: str, chapter_id: str = None) -> bool:
        """
        Validates a single chapter.

        Args:
            chapter_data: Chapter data dictionary
            file_path: Path to the chapter file (for error reporting)
            chapter_id: ID of the chapter (if known)

        Returns:
            True if the chapter is valid, False otherwise
        """
        # Get chapter ID from data or use provided ID
        chapter_id = chapter_data.get("chapter_id", chapter_id)
        if not chapter_id:
            logger.error(f"Chapter in {file_path} is missing chapter_id")
            return False

        # Check required fields
        required_fields = ["type", "title", "description"]
        for field in required_fields:
            if field not in chapter_data:
                logger.error(f"Chapter {chapter_id} in {file_path} is missing required field: {field}")
                return False

        # Check choices
        if "choices" not in chapter_data:
            logger.warning(f"Chapter {chapter_id} in {file_path} is missing 'choices' field")
            # Don't fail validation, but log a warning
        else:
            choices = chapter_data.get("choices", [])
            if not isinstance(choices, list):
                logger.error(f"Chapter {chapter_id} in {file_path}: 'choices' must be a list")
                return False

            # Validate each choice if there are any
            for i, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    logger.error(f"Chapter {chapter_id} in {file_path}: choice {i} must be a dictionary")
                    return False

                if "text" not in choice:
                    logger.error(f"Chapter {chapter_id} in {file_path}: choice {i} is missing required field 'text'")
                    return False

        # Validate dialogues if present
        dialogues = chapter_data.get("dialogues", [])
        if dialogues and isinstance(dialogues, list):
            for i, dialogue in enumerate(dialogues):
                if not isinstance(dialogue, dict):
                    logger.error(f"Chapter {chapter_id} in {file_path}: dialogue {i} must be a dictionary")
                    return False

                # Check for nested choices in dialogues
                if "choices" in dialogue:
                    dialogue_choices = dialogue["choices"]
                    if not isinstance(dialogue_choices, list):
                        logger.error(f"Chapter {chapter_id} in {file_path}: dialogue {i} 'choices' must be a list")
                        return False

                    for j, choice in enumerate(dialogue_choices):
                        if not isinstance(choice, dict):
                            logger.error(f"Chapter {chapter_id} in {file_path}: dialogue {i} choice {j} must be a dictionary")
                            return False

                        if "text" not in choice:
                            logger.error(f"Chapter {chapter_id} in {file_path}: dialogue {i} choice {j} is missing required field 'text'")
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
