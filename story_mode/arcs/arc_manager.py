from typing import Dict, List, Any, Optional
import logging
from .academic.academic_arc import AcademicArc
from .romance.romance_arc import RomanceArc
from .club.club_arc import ClubArc
from .main.main_arc import MainArc
from ..interfaces import Chapter

logger = logging.getLogger('tokugawa_bot')

class ArcManager:
    """
    Manages all story arcs and coordinates their interactions.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the arc manager.
        
        Args:
            data_dir: Base directory for story data
        """
        self.data_dir = data_dir
        
        # Initialize all arcs
        self.arcs = {
            "main": MainArc(data_dir),
            "academic": AcademicArc(data_dir),
            "romance": RomanceArc(data_dir),
            "club": ClubArc(data_dir)
        }
        
        logger.info("Arc manager initialized with all story arcs")
    
    def get_chapter(self, chapter_id: str) -> Optional[Chapter]:
        """
        Get a chapter from any arc by its ID.
        Handles chapter suffixes (e.g., "chapter_1_a").
        
        Args:
            chapter_id: ID of the chapter to retrieve
            
        Returns:
            Chapter object if found, None otherwise
        """
        # First try to get the exact chapter
        for arc in self.arcs.values():
            chapter = arc.get_chapter(chapter_id)
            if chapter:
                return chapter
                
        # If not found, try to find a chapter with the same base ID
        base_id = chapter_id.rsplit('_', 1)[0] if '_' in chapter_id else chapter_id
        for arc in self.arcs.values():
            chapter = arc.get_chapter(base_id)
            if chapter:
                # Create a new chapter instance with the suffixed ID
                chapter_data = chapter.chapter_data.copy()
                chapter_data["chapter_id"] = chapter_id
                return type(chapter)(chapter_id, chapter_data)
                
        return None
    
    def get_available_chapters(self, player_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get all available chapters across all arcs.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary mapping arc IDs to lists of available chapter IDs
        """
        available = {}
        for arc_id, arc in self.arcs.items():
            available[arc_id] = arc.get_available_chapters(player_data)
        return available
    
    def get_arc_status(self, player_data: Dict[str, Any], arc_id: str = None) -> Dict[str, Any]:
        """
        Get status information for one or all arcs.
        
        Args:
            player_data: Current player data
            arc_id: Optional specific arc to get status for
            
        Returns:
            Dictionary containing arc status information
        """
        if arc_id:
            if arc_id not in self.arcs:
                return {"error": f"Unknown arc: {arc_id}"}
            return self.arcs[arc_id].get_arc_status(player_data)
        
        # Get status for all arcs
        all_status = {}
        for arc_id, arc in self.arcs.items():
            all_status[arc_id] = arc.get_arc_status(player_data)
        return all_status
    
    def get_detailed_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed status information for all arcs and their interactions.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary containing detailed status information
        """
        # Get main story status
        main_status = self.arcs["main"].get_story_status(player_data)
        
        # Get academic status
        academic_status = self.arcs["academic"].get_academic_status(player_data)
        
        # Get romance status
        romance_status = self.arcs["romance"].get_romance_status(player_data)
        
        # Get club status
        club_status = self.arcs["club"].get_club_status(player_data)
        
        return {
            "main_story": main_status,
            "academic": academic_status,
            "romance": romance_status,
            "club": club_status,
            "available_chapters": self.get_available_chapters(player_data)
        }
    
    def process_chapter_completion(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Process the completion of a chapter and update all relevant arcs.
        
        Args:
            player_data: Current player data
            chapter_id: ID of the completed chapter
            
        Returns:
            Updated player data
        """
        # Find which arc the chapter belongs to
        chapter = self.get_chapter(chapter_id)
        if not chapter:
            logger.error(f"Unknown chapter: {chapter_id}")
            return player_data
        
        # Update story progress
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
        if chapter_id not in completed_chapters:
            completed_chapters.append(chapter_id)
            story_progress["completed_chapters"] = completed_chapters
        
        # Update arc-specific progress
        arc_type = chapter.chapter_data.get("arc_type")
        if arc_type in self.arcs:
            # Update progress in the specific arc
            arc = self.arcs[arc_type]
            arc_progress = story_progress.get(f"{arc_type}_progress", 0)
            progress_increase = chapter.chapter_data.get("progress_value", 1)
            story_progress[f"{arc_type}_progress"] = arc_progress + progress_increase
        
        # Check for main story phase advancement
        player_data = self.arcs["main"].advance_story_phase(player_data)
        
        # Update player data
        player_data["story_progress"] = story_progress
        
        return player_data
    
    def validate_story_structure(self) -> Dict[str, Any]:
        """
        Validate the entire story structure for consistency and completeness.
        
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "errors": [],
            "warnings": [],
            "arcs": {}
        }
        
        # Validate each arc
        for arc_id, arc in self.arcs.items():
            arc_validation = self._validate_arc(arc)
            validation_results["arcs"][arc_id] = arc_validation
            
            # Collect errors and warnings
            validation_results["errors"].extend(arc_validation.get("errors", []))
            validation_results["warnings"].extend(arc_validation.get("warnings", []))
        
        # Validate cross-arc dependencies
        cross_arc_validation = self._validate_cross_arc_dependencies()
        validation_results["errors"].extend(cross_arc_validation.get("errors", []))
        validation_results["warnings"].extend(cross_arc_validation.get("warnings", []))
        
        return validation_results
    
    def _validate_arc(self, arc: Any) -> Dict[str, Any]:
        """
        Validate a single arc's structure.
        
        Args:
            arc: Arc to validate
            
        Returns:
            Dictionary containing validation results
        """
        results = {
            "errors": [],
            "warnings": []
        }
        
        # Check for empty arcs
        if not arc.chapters:
            results["errors"].append(f"Arc {arc.arc_id} has no chapters")
            return results
        
        # Check for dead ends
        for chapter_id, chapter in arc.chapters.items():
            if not chapter.chapter_data.get("next_chapter") and not chapter.chapter_data.get("branches"):
                results["errors"].append(f"Dead end found in chapter {chapter_id}")
        
        # Check for missing prerequisites
        for chapter_id, chapter in arc.chapters.items():
            prerequisites = chapter.chapter_data.get("prerequisites", [])
            for prereq in prerequisites:
                if not self.get_chapter(prereq):
                    results["errors"].append(f"Missing prerequisite {prereq} for chapter {chapter_id}")
        
        return results
    
    def _validate_cross_arc_dependencies(self) -> Dict[str, Any]:
        """
        Validate dependencies between different arcs.
        
        Returns:
            Dictionary containing validation results
        """
        results = {
            "errors": [],
            "warnings": []
        }
        
        # Check main story requirements
        main_arc = self.arcs["main"]
        for phase, requirements in main_arc.required_progress.items():
            for arc, required in requirements.items():
                if arc not in self.arcs:
                    results["errors"].append(f"Main story requires unknown arc: {arc}")
        
        # Check for circular dependencies
        for arc_id, arc in self.arcs.items():
            for chapter_id, chapter in arc.chapters.items():
                dependencies = self._get_chapter_dependencies(chapter)
                if chapter_id in dependencies:
                    results["errors"].append(f"Circular dependency found in chapter {chapter_id}")
        
        return results
    
    def _get_chapter_dependencies(self, chapter: Chapter) -> List[str]:
        """
        Get all dependencies for a chapter.
        
        Args:
            chapter: Chapter to analyze
            
        Returns:
            List of chapter IDs that this chapter depends on
        """
        dependencies = []
        
        # Add prerequisites
        dependencies.extend(chapter.chapter_data.get("prerequisites", []))
        
        # Add special condition dependencies
        special_conditions = chapter.chapter_data.get("special_conditions", {})
        if "min_relationship" in special_conditions:
            character_id, _ = special_conditions["min_relationship"]
            # Find chapters that affect this relationship
            for arc in self.arcs.values():
                for chapter_id, ch in arc.chapters.items():
                    if ch.chapter_data.get("character_id") == character_id:
                        dependencies.append(chapter_id)
        
        return dependencies 