from typing import Dict, List, Any, Optional, Union, Set
import json
import os
import logging
import re
import sys
from collections import defaultdict, deque
from .chapter_validator import ChapterValidator

logger = logging.getLogger('tokugawa_bot')

class NarrativePathValidator:
    """
    Validates narrative paths in story mode chapters to ensure integrity and correctness.

    This validator checks for:
    1. Path integrity - ensuring all paths lead to valid destinations
    2. Broken references - detecting references to non-existent chapters
    3. Variable usage - validating that variables used in conditions are properly defined
    4. Path coverage - generating reports on narrative path coverage
    """

    def __init__(self, chapters_dir: str):
        """
        Initialize the validator with the directory containing chapter files.

        Args:
            chapters_dir: Path to the directory containing chapter JSON files
        """
        self.chapters_dir = chapters_dir
        self.chapters_data = {}
        self.chapter_files = {}
        self.referenced_chapters = set()
        self.defined_chapters = set()
        self.variable_usages = defaultdict(list)
        self.variable_definitions = defaultdict(list)
        self.path_coverage = {}

    def load_chapters(self) -> bool:
        """
        Load all chapter files from the chapters directory.

        Returns:
            True if all files were loaded successfully, False otherwise
        """
        if not os.path.exists(self.chapters_dir):
            logger.error(f"Chapters directory not found: {self.chapters_dir}")
            return False

        success = True
        for filename in os.listdir(self.chapters_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.chapters_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chapter_data = json.load(f)

                    # Store the mapping between chapter IDs and their source files
                    for chapter_id in chapter_data.keys():
                        self.chapters_data[chapter_id] = chapter_data[chapter_id]
                        self.chapter_files[chapter_id] = file_path
                        self.defined_chapters.add(chapter_id)

                except Exception as e:
                    logger.error(f"Error loading chapter file {file_path}: {e}")
                    success = False

        return success

    def validate_narrative_paths(self) -> bool:
        """
        Validate all narrative paths in the loaded chapters.

        Returns:
            True if all paths are valid, False otherwise
        """
        if not self.chapters_data:
            logger.error("No chapters loaded. Call load_chapters() first.")
            return False

        # Reset tracking variables
        self.referenced_chapters = set()
        self.variable_usages = defaultdict(list)
        self.variable_definitions = defaultdict(list)
        self.path_coverage = {chapter_id: {"total_paths": 0, "covered_paths": 0} for chapter_id in self.chapters_data}

        all_valid = True

        # First pass: collect all references and variable usages
        for chapter_id, chapter_data in self.chapters_data.items():
            if not self._collect_references_and_variables(chapter_id, chapter_data):
                all_valid = False

        # Second pass: validate references and variable usages
        for chapter_id, chapter_data in self.chapters_data.items():
            if not self._validate_chapter_paths(chapter_id, chapter_data):
                all_valid = False

        # Check for broken references
        broken_references = self.referenced_chapters - self.defined_chapters
        if broken_references:
            logger.error(f"Found broken chapter references: {broken_references}")
            all_valid = False

        # Check for undefined variables
        for var_name, usages in self.variable_usages.items():
            if var_name not in self.variable_definitions:
                logger.error(f"Variable '{var_name}' is used but never defined. Usages in: {usages}")
                all_valid = False

        return all_valid

    def _collect_references_and_variables(self, chapter_id: str, chapter_data: Dict[str, Any]) -> bool:
        """
        Collect all chapter references and variable usages in a chapter.

        Args:
            chapter_id: ID of the chapter
            chapter_data: Chapter data dictionary

        Returns:
            True if collection was successful, False otherwise
        """
        try:
            # Check next_chapter reference
            if "next_chapter" in chapter_data:
                next_chapter = chapter_data["next_chapter"]
                self.referenced_chapters.add(next_chapter)

            # Check conditional_next_chapter references
            if "conditional_next_chapter" in chapter_data:
                conditional = chapter_data["conditional_next_chapter"]
                self._process_conditional_next_chapter(conditional, chapter_id)

            # Check choices
            self._process_choices(chapter_data.get("choices", []), chapter_id)

            # Check dialogues and their choices
            for dialogue in chapter_data.get("dialogues", []):
                self._process_choices(dialogue.get("choices", []), chapter_id)

            # Check additional dialogues
            for dialogue_id, dialogues in chapter_data.get("additional_dialogues", {}).items():
                for dialogue in dialogues:
                    self._process_choices(dialogue.get("choices", []), chapter_id)

            return True
        except Exception as e:
            logger.error(f"Error collecting references in chapter {chapter_id}: {e}")
            return False

    def _process_conditional_next_chapter(self, conditional: Dict[str, Any], chapter_id: str):
        """
        Process conditional_next_chapter to collect references and variable usages.

        Args:
            conditional: Conditional next chapter dictionary
            chapter_id: ID of the current chapter
        """
        for var_name, conditions in conditional.items():
            # Record variable usage
            self.variable_usages[var_name].append(chapter_id)

            if isinstance(conditions, dict):
                # Handle dictionary of conditions
                for value, next_chapter in conditions.items():
                    if next_chapter and value != "default":
                        self.referenced_chapters.add(next_chapter)
            elif isinstance(conditions, str):
                # Handle direct chapter reference
                self.referenced_chapters.add(conditions)

    def _process_choices(self, choices: List[Dict[str, Any]], chapter_id: str):
        """
        Process choices to collect references and variable usages.

        Args:
            choices: List of choice dictionaries
            chapter_id: ID of the current chapter
        """
        for choice in choices:
            # Check next_chapter reference
            if "next_chapter" in choice:
                next_chapter = choice["next_chapter"]
                self.referenced_chapters.add(next_chapter)

            # Check for variable definitions in metadata
            metadata = choice.get("metadata", {})
            for key, value in metadata.items():
                # Record variable definition
                self.variable_definitions[key].append(chapter_id)

    def _validate_chapter_paths(self, chapter_id: str, chapter_data: Dict[str, Any]) -> bool:
        """
        Validate all paths in a chapter.

        Args:
            chapter_id: ID of the chapter
            chapter_data: Chapter data dictionary

        Returns:
            True if all paths are valid, False otherwise
        """
        valid = True

        # Count total possible paths
        total_paths = self._count_total_paths(chapter_data)
        self.path_coverage[chapter_id]["total_paths"] = total_paths

        # Validate next_chapter
        if "next_chapter" in chapter_data:
            next_chapter = chapter_data["next_chapter"]
            if next_chapter not in self.defined_chapters:
                logger.error(f"Chapter {chapter_id} references non-existent chapter: {next_chapter}")
                valid = False

        # Validate conditional_next_chapter
        if "conditional_next_chapter" in chapter_data:
            conditional = chapter_data["conditional_next_chapter"]
            if not self._validate_conditional_next_chapter(conditional, chapter_id):
                valid = False

        # Validate choices
        if not self._validate_choices(chapter_data.get("choices", []), chapter_id):
            valid = False

        # Validate dialogues and their choices
        for dialogue in chapter_data.get("dialogues", []):
            if not self._validate_choices(dialogue.get("choices", []), chapter_id):
                valid = False

        # Validate additional dialogues
        for dialogue_id, dialogues in chapter_data.get("additional_dialogues", {}).items():
            for dialogue in dialogues:
                if not self._validate_choices(dialogue.get("choices", []), chapter_id):
                    valid = False

        return valid

    def _validate_conditional_next_chapter(self, conditional: Dict[str, Any], chapter_id: str) -> bool:
        """
        Validate conditional_next_chapter references.

        Args:
            conditional: Conditional next chapter dictionary
            chapter_id: ID of the current chapter

        Returns:
            True if all references are valid, False otherwise
        """
        valid = True

        for var_name, conditions in conditional.items():
            if isinstance(conditions, dict):
                # Handle dictionary of conditions
                for value, next_chapter in conditions.items():
                    if next_chapter and value != "default" and next_chapter not in self.defined_chapters:
                        logger.error(f"Chapter {chapter_id} conditional references non-existent chapter: {next_chapter}")
                        valid = False
            elif isinstance(conditions, str) and conditions not in self.defined_chapters:
                # Handle direct chapter reference
                logger.error(f"Chapter {chapter_id} conditional references non-existent chapter: {conditions}")
                valid = False

        return valid

    def _validate_choices(self, choices: List[Dict[str, Any]], chapter_id: str) -> bool:
        """
        Validate choices and their references.

        Args:
            choices: List of choice dictionaries
            chapter_id: ID of the current chapter

        Returns:
            True if all choices are valid, False otherwise
        """
        valid = True

        for choice in choices:
            # Validate next_chapter reference
            if "next_chapter" in choice:
                next_chapter = choice["next_chapter"]
                if next_chapter not in self.defined_chapters:
                    logger.error(f"Chapter {chapter_id} choice references non-existent chapter: {next_chapter}")
                    valid = False

        return valid

    def _count_total_paths(self, chapter_data: Dict[str, Any]) -> int:
        """
        Count the total number of possible paths through a chapter.

        Args:
            chapter_data: Chapter data dictionary

        Returns:
            Total number of possible paths
        """
        # This is a simplified count - a more accurate count would require traversing all possible combinations
        path_count = 0

        # Count direct next_chapter
        if "next_chapter" in chapter_data:
            path_count += 1

        # Count conditional next chapters
        if "conditional_next_chapter" in chapter_data:
            conditional = chapter_data["conditional_next_chapter"]
            for var_name, conditions in conditional.items():
                if isinstance(conditions, dict):
                    path_count += len(conditions)
                else:
                    path_count += 1

        # Count choices
        path_count += len(chapter_data.get("choices", []))

        # Count dialogue choices
        for dialogue in chapter_data.get("dialogues", []):
            path_count += len(dialogue.get("choices", []))

        # Count additional dialogue choices
        for dialogue_id, dialogues in chapter_data.get("additional_dialogues", {}).items():
            for dialogue in dialogues:
                path_count += len(dialogue.get("choices", []))

        return path_count

    def generate_coverage_report(self) -> Dict[str, Any]:
        """
        Generate a report on narrative path coverage.

        Returns:
            Dictionary containing coverage statistics
        """
        total_paths = sum(data["total_paths"] for data in self.path_coverage.values())
        covered_paths = sum(data["covered_paths"] for data in self.path_coverage.values())

        coverage_percentage = (covered_paths / total_paths * 100) if total_paths > 0 else 0

        report = {
            "total_chapters": len(self.defined_chapters),
            "total_paths": total_paths,
            "covered_paths": covered_paths,
            "coverage_percentage": coverage_percentage,
            "chapter_coverage": self.path_coverage,
            "broken_references": list(self.referenced_chapters - self.defined_chapters),
            "undefined_variables": [var for var in self.variable_usages if var not in self.variable_definitions]
        }

        return report

    def simulate_path_coverage(self) -> None:
        """
        Simulate path traversal to estimate path coverage.
        This is a simplified simulation and doesn't account for all possible combinations.
        """
        visited = set()
        queue = deque(["1_1"])  # Start with the first chapter

        while queue:
            chapter_id = queue.popleft()

            if chapter_id in visited or chapter_id not in self.chapters_data:
                continue

            visited.add(chapter_id)
            chapter_data = self.chapters_data[chapter_id]

            # Mark this chapter's paths as covered
            if chapter_id in self.path_coverage:
                self.path_coverage[chapter_id]["covered_paths"] = self.path_coverage[chapter_id]["total_paths"]

            # Add next chapters to the queue
            if "next_chapter" in chapter_data:
                queue.append(chapter_data["next_chapter"])

            # Add conditional next chapters
            if "conditional_next_chapter" in chapter_data:
                conditional = chapter_data["conditional_next_chapter"]
                for var_name, conditions in conditional.items():
                    if isinstance(conditions, dict):
                        for value, next_chapter in conditions.items():
                            if next_chapter:
                                queue.append(next_chapter)
                    elif isinstance(conditions, str):
                        queue.append(conditions)

            # Add choices next chapters
            for choice in chapter_data.get("choices", []):
                if "next_chapter" in choice:
                    queue.append(choice["next_chapter"])

            # Add dialogue choices next chapters
            for dialogue in chapter_data.get("dialogues", []):
                for choice in dialogue.get("choices", []):
                    if "next_chapter" in choice:
                        queue.append(choice["next_chapter"])

            # Add additional dialogue choices next chapters
            for dialogue_id, dialogues in chapter_data.get("additional_dialogues", {}).items():
                for dialogue in dialogues:
                    for choice in dialogue.get("choices", []):
                        if "next_chapter" in choice:
                            queue.append(choice["next_chapter"])

def validate_narrative_paths_cli():
    """
    Command-line interface for validating narrative paths.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m story_mode.narrative_validator <chapters_dir>")
        return False

    chapters_dir = sys.argv[1]
    validator = NarrativePathValidator(chapters_dir)

    print(f"Loading chapters from {chapters_dir}...")
    if not validator.load_chapters():
        print("Failed to load chapters.")
        return False

    print(f"Loaded {len(validator.chapters_data)} chapters.")
    print("Validating narrative paths...")

    valid = validator.validate_narrative_paths()

    print("Simulating path coverage...")
    validator.simulate_path_coverage()

    report = validator.generate_coverage_report()

    print("\nNarrative Path Validation Report:")
    print(f"Total Chapters: {report['total_chapters']}")
    print(f"Total Paths: {report['total_paths']}")
    print(f"Covered Paths: {report['covered_paths']}")
    print(f"Coverage Percentage: {report['coverage_percentage']:.2f}%")

    if report['broken_references']:
        print(f"\nBroken References ({len(report['broken_references'])}):")
        for ref in report['broken_references']:
            print(f"  - {ref}")

    if report['undefined_variables']:
        print(f"\nUndefined Variables ({len(report['undefined_variables'])}):")
        for var in report['undefined_variables']:
            print(f"  - {var}")

    return valid

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run validator
    success = validate_narrative_paths_cli()
    sys.exit(0 if success else 1)
