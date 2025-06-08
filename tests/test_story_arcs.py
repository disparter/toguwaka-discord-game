import unittest
import json
import os
from story_mode.arcs.arc_manager import ArcManager
from story_mode.arcs.academic.academic_arc import AcademicArc
from story_mode.arcs.romance.romance_arc import RomanceArc
from story_mode.arcs.club.club_arc import ClubArc
from story_mode.arcs.main.main_arc import MainArc

class TestStoryArcs(unittest.TestCase):
    """
    Test suite for the story arc system.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        self.data_dir = "data/story_mode"
        self.arc_manager = ArcManager(self.data_dir)
        
        # Create test player data
        self.player_data = {
            "story_progress": {
                "current_phase": "prologue",
                "completed_chapters": [],
                "academic_progress": 0,
                "club_progress": 0,
                "romance_progress": 0
            },
            "relationships": {},
            "club_data": {},
            "factions": {},
            "attributes": {
                "power_stat": 10,
                "intellect": 10,
                "charisma": 10,
                "dexterity": 10
            }
        }
    
    def test_arc_initialization(self):
        """
        Test that all arcs are properly initialized with correct dependencies.
        """
        # Check arc existence
        self.assertIn("main", self.arc_manager.arcs)
        self.assertIn("academic", self.arc_manager.arcs)
        self.assertIn("romance", self.arc_manager.arcs)
        self.assertIn("club", self.arc_manager.arcs)
        
        # Check arc types
        self.assertIsInstance(self.arc_manager.arcs["main"], MainArc)
        self.assertIsInstance(self.arc_manager.arcs["academic"], AcademicArc)
        self.assertIsInstance(self.arc_manager.arcs["romance"], RomanceArc)
        self.assertIsInstance(self.arc_manager.arcs["club"], ClubArc)
        
        # Check arc dependencies
        main_arc = self.arc_manager.arcs["main"]
        self.assertIn("academic", main_arc.required_arcs)
        self.assertIn("club", main_arc.required_arcs)
        self.assertIn("romance", main_arc.required_arcs)
    
    def test_chapter_loading_and_validation(self):
        """
        Test that chapters are properly loaded and validated.
        """
        # Check chapter loading
        for arc_id, arc in self.arc_manager.arcs.items():
            self.assertGreater(len(arc.chapters), 0, f"Arc {arc_id} has no chapters")
            
            # Validate chapter structure
            for chapter_id, chapter in arc.chapters.items():
                self.assertIn("type", chapter)
                self.assertIn("title", chapter)
                self.assertIn("description", chapter)
                self.assertIn("dialogues", chapter)
                self.assertIn("choices", chapter)
                
                # Validate chapter dependencies
                if "required_progress" in chapter:
                    self.assertIsInstance(chapter["required_progress"], dict)
    
    def test_chapter_availability_logic(self):
        """
        Test the logic for determining available chapters.
        """
        # Get initial available chapters
        initial_available = self.arc_manager.get_available_chapters(self.player_data)
        
        # Check that each arc has available chapters
        for arc_id, chapters in initial_available.items():
            self.assertGreater(len(chapters), 0, f"No available chapters in arc {arc_id}")
            
            # Verify chapter requirements
            for chapter_id in chapters:
                chapter = self.arc_manager.get_chapter(chapter_id)
                if "required_progress" in chapter:
                    for arc, progress in chapter["required_progress"].items():
                        self.assertLessEqual(
                            self.player_data["story_progress"][f"{arc}_progress"],
                            progress,
                            f"Chapter {chapter_id} should not be available with current progress"
                        )
    
    def test_story_progression_and_dependencies(self):
        """
        Test story progression and arc dependencies.
        """
        # Complete a chapter in each arc
        for arc_id in ["academic", "club", "romance"]:
            available = self.arc_manager.get_available_chapters(self.player_data)
            if arc_id in available and available[arc_id]:
                chapter_id = next(iter(available[arc_id]))
                self.player_data = self.arc_manager.process_chapter_completion(
                    self.player_data, chapter_id
                )
        
        # Check that main story chapters become available
        main_available = self.arc_manager.get_available_chapters(self.player_data)
        self.assertGreater(len(main_available["main"]), 0, "Main story chapters should be available")
    
    def test_arc_interactions(self):
        """
        Test interactions between different arcs.
        """
        # Get initial status
        initial_status = self.arc_manager.get_detailed_status(self.player_data)
        
        # Complete a chapter in each arc
        for arc_id in ["academic", "club", "romance"]:
            available = self.arc_manager.get_available_chapters(self.player_data)
            if arc_id in available and available[arc_id]:
                chapter_id = next(iter(available[arc_id]))
                self.player_data = self.arc_manager.process_chapter_completion(
                    self.player_data, chapter_id
                )
        
        # Get new status
        new_status = self.arc_manager.get_detailed_status(self.player_data)
        
        # Check that arc progress affects main story
        self.assertNotEqual(
            new_status["main_story"]["arc_progress"],
            initial_status["main_story"]["arc_progress"]
        )
        
        # Check that arc interactions are properly tracked
        for arc_id in ["academic", "club", "romance"]:
            self.assertIn(arc_id, new_status["main_story"]["arc_progress"])
            self.assertGreater(
                new_status["main_story"]["arc_progress"][arc_id],
                initial_status["main_story"]["arc_progress"][arc_id]
            )
    
    def test_story_validation(self):
        """
        Test story structure validation.
        """
        validation_results = self.arc_manager.validate_story_structure()
        
        # Check for validation errors
        self.assertEqual(len(validation_results["errors"]), 0, 
                        f"Story validation errors: {validation_results['errors']}")
        
        # Check for validation warnings
        self.assertEqual(len(validation_results["warnings"]), 0,
                        f"Story validation warnings: {validation_results['warnings']}")
        
        # Verify chapter connectivity
        self.assertTrue(validation_results["is_connected"],
                       "Story chapters should form a connected graph")
        
        # Verify no dead ends
        self.assertTrue(validation_results["no_dead_ends"],
                       "Story should not have dead ends")
    
    def test_relationship_progression(self):
        """
        Test relationship progression in romance arc.
        """
        # Initialize a relationship
        character_id = "test_character"
        self.player_data["relationships"] = {
            character_id: {
                "affinity": 0,
                "status": "stranger",
                "events": []
            }
        }
        
        # Get initial status
        initial_status = self.arc_manager.arcs["romance"].get_romance_status(
            self.player_data, character_id
        )
        
        # Update affinity through multiple events
        for affinity_change in [30, 20, 50]:
            self.player_data = self.arc_manager.arcs["romance"].update_affinity(
                self.player_data, character_id, affinity_change
            )
        
        # Get new status
        new_status = self.arc_manager.arcs["romance"].get_romance_status(
            self.player_data, character_id
        )
        
        # Check relationship progression
        self.assertGreater(new_status["affinity"], initial_status["affinity"])
        self.assertNotEqual(new_status["status"], initial_status["status"])
        self.assertGreater(len(new_status["events"]), len(initial_status["events"]))
    
    def test_club_progression(self):
        """
        Test club progression and activities.
        """
        # Initialize club data
        club_id = "test_club"
        self.player_data["club_data"] = {
            club_id: {
                "experience": 0,
                "attendance": 0,
                "achievements": [],
                "missions": [],
                "rank": 1
            }
        }
        
        # Get initial status
        initial_status = self.arc_manager.arcs["club"].get_club_status(
            self.player_data, club_id
        )
        
        # Simulate club activities
        activities = [
            {"type": "mission", "experience": 40},
            {"type": "event", "experience": 20},
            {"type": "competition", "experience": 60}
        ]
        
        for activity in activities:
            self.player_data = self.arc_manager.arcs["club"].process_activity(
                self.player_data, club_id, activity
            )
        
        # Get new status
        new_status = self.arc_manager.arcs["club"].get_club_status(
            self.player_data, club_id
        )
        
        # Check club progression
        self.assertGreater(new_status["experience"], initial_status["experience"])
        self.assertGreaterEqual(new_status["rank"], initial_status["rank"])
        self.assertGreater(len(new_status["achievements"]), len(initial_status["achievements"]))
    
    def test_academic_progression(self):
        """
        Test academic progression and course completion.
        """
        # Initialize academic progress
        self.player_data["academic_progress"] = {
            "current_year": 1,
            "current_gpa": 0,
            "completed_courses": [],
            "current_courses": [],
            "achievements": []
        }
        
        # Get initial status
        initial_status = self.arc_manager.arcs["academic"].get_academic_status(self.player_data)
        
        # Simulate academic activities
        activities = [
            {"type": "course", "name": "history", "grade": 85},
            {"type": "exam", "course": "history", "grade": 90},
            {"type": "project", "course": "history", "grade": 95}
        ]
        
        for activity in activities:
            self.player_data = self.arc_manager.arcs["academic"].process_activity(
                self.player_data, activity
            )
        
        # Get new status
        new_status = self.arc_manager.arcs["academic"].get_academic_status(self.player_data)
        
        # Check academic progression
        self.assertGreater(new_status["current_gpa"], initial_status["current_gpa"])
        self.assertGreater(len(new_status["completed_courses"]), len(initial_status["completed_courses"]))
        self.assertGreater(len(new_status["achievements"]), len(initial_status["achievements"]))
    
    def test_main_story_phases(self):
        """
        Test main story phase progression and requirements.
        """
        # Get initial status
        initial_status = self.arc_manager.arcs["main"].get_story_status(self.player_data)
        
        # Simulate progress in all arcs
        arc_progress = {
            "academic": 30,
            "club": 20,
            "romance": 10
        }
        
        for arc, progress in arc_progress.items():
            self.player_data["story_progress"][f"{arc}_progress"] = progress
        
        # Try to advance phase
        self.player_data = self.arc_manager.arcs["main"].advance_story_phase(self.player_data)
        
        # Get new status
        new_status = self.arc_manager.arcs["main"].get_story_status(self.player_data)
        
        # Check phase progression
        self.assertNotEqual(new_status["current_phase"], initial_status["current_phase"])
        self.assertGreater(new_status["overall_progress"], initial_status["overall_progress"])
        
        # Verify phase requirements
        for arc, progress in arc_progress.items():
            self.assertGreaterEqual(
                new_status["arc_progress"][arc],
                progress,
                f"Phase advancement should maintain {arc} progress"
            )

    def test_parallel_arc_progression(self):
        """
        Test that multiple arcs can progress in parallel without interference.
        """
        # Initialize progress in all arcs
        for arc_id in ["academic", "club", "romance"]:
            self.player_data["story_progress"][f"{arc_id}_progress"] = 10
        
        # Get initial status
        initial_status = self.arc_manager.get_detailed_status(self.player_data)
        
        # Progress in each arc simultaneously
        for arc_id in ["academic", "club", "romance"]:
            available = self.arc_manager.get_available_chapters(self.player_data)
            if arc_id in available and available[arc_id]:
                chapter_id = next(iter(available[arc_id]))
                self.player_data = self.arc_manager.process_chapter_completion(
                    self.player_data, chapter_id
                )
        
        # Get new status
        new_status = self.arc_manager.get_detailed_status(self.player_data)
        
        # Verify each arc progressed independently
        for arc_id in ["academic", "club", "romance"]:
            self.assertGreater(
                new_status["arc_progress"][arc_id],
                initial_status["arc_progress"][arc_id],
                f"{arc_id} arc should progress independently"
            )
    
    def test_arc_restrictions(self):
        """
        Test that arc restrictions are properly enforced.
        """
        # Set up restrictions
        self.player_data["story_progress"]["academic_progress"] = 20
        self.player_data["story_progress"]["club_progress"] = 10
        self.player_data["story_progress"]["romance_progress"] = 5
        
        # Try to access restricted chapters
        available = self.arc_manager.get_available_chapters(self.player_data)
        
        for arc_id, chapters in available.items():
            for chapter_id in chapters:
                chapter = self.arc_manager.get_chapter(chapter_id)
                if "required_progress" in chapter:
                    for req_arc, req_progress in chapter["required_progress"].items():
                        self.assertLessEqual(
                            self.player_data["story_progress"][f"{req_arc}_progress"],
                            req_progress,
                            f"Chapter {chapter_id} should not be available with current {req_arc} progress"
                        )
    
    def test_achievement_system(self):
        """
        Test the achievement system across all arcs.
        """
        # Initialize achievement tracking
        self.player_data["achievements"] = {
            "academic": [],
            "club": [],
            "romance": [],
            "main": []
        }
        
        # Simulate activities that should trigger achievements
        activities = [
            {"arc": "academic", "type": "course_completion", "grade": 95},
            {"arc": "club", "type": "competition_win", "rank": 1},
            {"arc": "romance", "type": "relationship_milestone", "level": "close_friend"}
        ]
        
        for activity in activities:
            arc = self.arc_manager.arcs[activity["arc"]]
            self.player_data = arc.process_activity(self.player_data, activity)
        
        # Verify achievements were properly awarded
        for arc_id in ["academic", "club", "romance", "main"]:
            self.assertGreater(
                len(self.player_data["achievements"][arc_id]),
                0,
                f"No achievements awarded for {arc_id} arc"
            )
    
    def test_story_branching(self):
        """
        Test that story branches are properly handled and tracked.
        """
        # Initialize branching data
        self.player_data["story_branches"] = {
            "academic": {"path": "scholarship"},
            "club": {"path": "leadership"},
            "romance": {"path": "friendship"}
        }
        
        # Get initial status
        initial_status = self.arc_manager.get_detailed_status(self.player_data)
        
        # Progress through branches
        for arc_id in ["academic", "club", "romance"]:
            available = self.arc_manager.get_available_chapters(self.player_data)
            if arc_id in available and available[arc_id]:
                chapter_id = next(iter(available[arc_id]))
                self.player_data = self.arc_manager.process_chapter_completion(
                    self.player_data, chapter_id
                )
        
        # Verify branch progression
        new_status = self.arc_manager.get_detailed_status(self.player_data)
        for arc_id in ["academic", "club", "romance"]:
            self.assertIn(
                "branch_progress",
                new_status["arc_progress"][arc_id],
                f"Branch progress not tracked for {arc_id}"
            )
    
    def test_arc_completion(self):
        """
        Test arc completion and rewards.
        """
        # Set up near-completion state
        for arc_id in ["academic", "club", "romance"]:
            self.player_data["story_progress"][f"{arc_id}_progress"] = 90
        
        # Complete final chapters
        for arc_id in ["academic", "club", "romance"]:
            available = self.arc_manager.get_available_chapters(self.player_data)
            if arc_id in available and available[arc_id]:
                chapter_id = next(iter(available[arc_id]))
                self.player_data = self.arc_manager.process_chapter_completion(
                    self.player_data, chapter_id
                )
        
        # Verify arc completion
        status = self.arc_manager.get_detailed_status(self.player_data)
        for arc_id in ["academic", "club", "romance"]:
            self.assertTrue(
                status["arc_progress"][arc_id]["completed"],
                f"{arc_id} arc should be marked as completed"
            )
            self.assertIn(
                "completion_rewards",
                status["arc_progress"][arc_id],
                f"No completion rewards for {arc_id} arc"
            )
    
    def test_cross_arc_events(self):
        """
        Test events that affect multiple arcs simultaneously.
        """
        # Initialize cross-arc event data
        self.player_data["cross_arc_events"] = []
        
        # Simulate cross-arc events
        events = [
            {
                "type": "school_festival",
                "affected_arcs": ["academic", "club", "romance"],
                "impact": {"academic": 10, "club": 15, "romance": 5}
            },
            {
                "type": "exam_period",
                "affected_arcs": ["academic", "romance"],
                "impact": {"academic": 20, "romance": -5}
            }
        ]
        
        for event in events:
            self.player_data = self.arc_manager.process_cross_arc_event(
                self.player_data, event
            )
        
        # Verify cross-arc impacts
        status = self.arc_manager.get_detailed_status(self.player_data)
        for event in events:
            for arc_id, impact in event["impact"].items():
                self.assertIn(
                    event["type"],
                    status["arc_progress"][arc_id]["recent_events"],
                    f"Cross-arc event {event['type']} not recorded for {arc_id}"
                )
    
    def test_arc_synchronization(self):
        """
        Test that arcs stay synchronized with the main story.
        """
        # Set up initial state
        self.player_data["story_progress"]["current_phase"] = "chapter_1"
        
        # Progress through main story
        main_arc = self.arc_manager.arcs["main"]
        available = self.arc_manager.get_available_chapters(self.player_data)
        if "main" in available and available["main"]:
            chapter_id = next(iter(available["main"]))
            self.player_data = main_arc.process_chapter_completion(
                self.player_data, chapter_id
            )
        
        # Verify other arcs are synchronized
        status = self.arc_manager.get_detailed_status(self.player_data)
        for arc_id in ["academic", "club", "romance"]:
            self.assertEqual(
                status["arc_progress"][arc_id]["story_phase"],
                self.player_data["story_progress"]["current_phase"],
                f"{arc_id} arc not synchronized with main story"
            )
    
    def test_arc_rewards(self):
        """
        Test that arc rewards are properly distributed and tracked.
        """
        # Initialize reward tracking
        self.player_data["arc_rewards"] = {
            "academic": [],
            "club": [],
            "romance": [],
            "main": []
        }
        
        # Simulate activities that should grant rewards
        activities = [
            {"arc": "academic", "type": "exam", "grade": 95},
            {"arc": "club", "type": "tournament", "placement": 1},
            {"arc": "romance", "type": "date", "success": True}
        ]
        
        for activity in activities:
            arc = self.arc_manager.arcs[activity["arc"]]
            self.player_data = arc.process_activity(self.player_data, activity)
        
        # Verify rewards were properly granted
        for arc_id in ["academic", "club", "romance", "main"]:
            self.assertGreater(
                len(self.player_data["arc_rewards"][arc_id]),
                0,
                f"No rewards granted for {arc_id} arc"
            )
            
            # Verify reward types
            for reward in self.player_data["arc_rewards"][arc_id]:
                self.assertIn("type", reward)
                self.assertIn("value", reward)
                self.assertIn("description", reward)

    def test_arc_state_persistence(self):
        """
        Test that arc states are properly persisted and restored.
        """
        # Initialize arc states
        initial_states = {
            "academic": {"current_course": "math", "attendance": 5},
            "club": {"current_activity": "training", "membership_days": 10},
            "romance": {"current_interest": "character1", "interaction_count": 3}
        }
        
        # Set states
        for arc_id, state in initial_states.items():
            self.player_data[f"{arc_id}_state"] = state
        
        # Save and restore states
        saved_data = self.arc_manager.save_arc_states(self.player_data)
        restored_data = self.arc_manager.restore_arc_states(saved_data)
        
        # Verify state persistence
        for arc_id, state in initial_states.items():
            self.assertEqual(
                restored_data[f"{arc_id}_state"],
                state,
                f"{arc_id} state not properly persisted"
            )
    
    def test_arc_conflict_resolution(self):
        """
        Test resolution of conflicts between different arcs.
        """
        # Set up conflicting states
        self.player_data["story_progress"]["academic_progress"] = 50
        self.player_data["story_progress"]["club_progress"] = 50
        self.player_data["story_progress"]["romance_progress"] = 50
        
        # Create conflicting events
        conflicts = [
            {
                "type": "exam_conflict",
                "arcs": ["academic", "club"],
                "resolution": "prioritize_academic"
            },
            {
                "type": "date_conflict",
                "arcs": ["romance", "club"],
                "resolution": "split_time"
            }
        ]
        
        # Process conflicts
        for conflict in conflicts:
            resolution = self.arc_manager.resolve_arc_conflict(
                self.player_data, conflict
            )
            
            # Verify conflict resolution
            self.assertIn("resolution", resolution)
            self.assertIn("impact", resolution)
            for arc_id in conflict["arcs"]:
                self.assertIn(arc_id, resolution["impact"])
    
    def test_arc_stat_influence(self):
        """
        Test how player stats influence arc progression.
        """
        # Set up different stat configurations
        stat_configs = [
            {"intellect": 20, "charisma": 10, "dexterity": 10},
            {"intellect": 10, "charisma": 20, "dexterity": 10},
            {"intellect": 10, "charisma": 10, "dexterity": 20}
        ]
        
        for stats in stat_configs:
            self.player_data["attributes"].update(stats)
            
            # Check arc availability and requirements
            available = self.arc_manager.get_available_chapters(self.player_data)
            
            for arc_id, chapters in available.items():
                for chapter_id in chapters:
                    chapter = self.arc_manager.get_chapter(chapter_id)
                    if "stat_requirements" in chapter:
                        for stat, value in chapter["stat_requirements"].items():
                            self.assertGreaterEqual(
                                self.player_data["attributes"][stat],
                                value,
                                f"Chapter {chapter_id} should not be available with current {stat}"
                            )
    
    def test_arc_time_management(self):
        """
        Test time management and scheduling across arcs.
        """
        # Initialize time tracking
        self.player_data["time_management"] = {
            "current_week": 1,
            "daily_schedule": {},
            "weekly_events": []
        }
        
        # Add activities to schedule
        activities = [
            {"arc": "academic", "type": "class", "duration": 2, "day": "monday"},
            {"arc": "club", "type": "practice", "duration": 3, "day": "wednesday"},
            {"arc": "romance", "type": "date", "duration": 4, "day": "friday"}
        ]
        
        for activity in activities:
            self.player_data = self.arc_manager.schedule_activity(
                self.player_data, activity
            )
        
        # Verify schedule management
        schedule = self.player_data["time_management"]["daily_schedule"]
        for day in ["monday", "wednesday", "friday"]:
            self.assertIn(day, schedule)
            self.assertGreater(len(schedule[day]), 0)
            
            # Check for schedule conflicts
            total_duration = sum(act["duration"] for act in schedule[day])
            self.assertLessEqual(total_duration, 8, f"Schedule conflict on {day}")
    
    def test_arc_reputation_system(self):
        """
        Test the reputation system across different arcs.
        """
        # Initialize reputation tracking
        self.player_data["reputation"] = {
            "academic": {"faculty": 0, "students": 0},
            "club": {"members": 0, "rivals": 0},
            "romance": {"characters": {}}
        }
        
        # Simulate reputation changes
        reputation_events = [
            {"arc": "academic", "type": "good_grades", "impact": {"faculty": 10, "students": 5}},
            {"arc": "club", "type": "tournament_win", "impact": {"members": 15, "rivals": -5}},
            {"arc": "romance", "type": "gift", "impact": {"character1": 20}}
        ]
        
        for event in reputation_events:
            self.player_data = self.arc_manager.update_reputation(
                self.player_data, event
            )
        
        # Verify reputation changes
        for arc_id in ["academic", "club", "romance"]:
            arc_reputation = self.player_data["reputation"][arc_id]
            if arc_id == "romance":
                self.assertGreater(
                    arc_reputation["characters"]["character1"],
                    0,
                    "Romance reputation not properly updated"
                )
            else:
                for group, value in arc_reputation.items():
                    self.assertNotEqual(value, 0, f"{arc_id} {group} reputation not updated")
    
    def test_arc_skill_progression(self):
        """
        Test skill progression within each arc.
        """
        # Initialize skill tracking
        self.player_data["skills"] = {
            "academic": {"study": 0, "research": 0},
            "club": {"teamwork": 0, "leadership": 0},
            "romance": {"communication": 0, "empathy": 0}
        }
        
        # Simulate skill development
        skill_activities = [
            {"arc": "academic", "type": "study_session", "skills": ["study"]},
            {"arc": "club", "type": "team_practice", "skills": ["teamwork", "leadership"]},
            {"arc": "romance", "type": "heart_to_heart", "skills": ["communication", "empathy"]}
        ]
        
        for activity in skill_activities:
            self.player_data = self.arc_manager.develop_skills(
                self.player_data, activity
            )
        
        # Verify skill progression
        for arc_id in ["academic", "club", "romance"]:
            arc_skills = self.player_data["skills"][arc_id]
            for skill, level in arc_skills.items():
                self.assertGreater(level, 0, f"{arc_id} {skill} not improved")
    
    def test_arc_choice_consequences(self):
        """
        Test the consequences of choices across different arcs.
        """
        # Initialize choice tracking
        self.player_data["choices"] = {
            "academic": [],
            "club": [],
            "romance": [],
            "main": []
        }
        
        # Simulate choices and their consequences
        choices = [
            {
                "arc": "academic",
                "choice": "study_hard",
                "consequences": {
                    "academic_progress": 10,
                    "club_progress": -5,
                    "romance_progress": -5
                }
            },
            {
                "arc": "club",
                "choice": "skip_practice",
                "consequences": {
                    "club_progress": -10,
                    "reputation": {"members": -5}
                }
            }
        ]
        
        for choice in choices:
            self.player_data = self.arc_manager.process_choice_consequences(
                self.player_data, choice
            )
        
        # Verify choice consequences
        for choice in choices:
            arc_id = choice["arc"]
            self.assertIn(choice["choice"], self.player_data["choices"][arc_id])
            
            # Check progress impacts
            for progress_type, impact in choice["consequences"].items():
                if progress_type.endswith("_progress"):
                    self.assertNotEqual(
                        self.player_data["story_progress"][progress_type],
                        0,
                        f"{progress_type} not affected by choice"
                    )
    
    def test_arc_achievement_unlocking(self):
        """
        Test the achievement unlocking system across arcs.
        """
        # Initialize achievement tracking
        self.player_data["achievements"] = {
            "academic": {"unlocked": [], "locked": ["straight_a", "research_paper"]},
            "club": {"unlocked": [], "locked": ["tournament_champion", "team_captain"]},
            "romance": {"unlocked": [], "locked": ["true_love", "social_butterfly"]}
        }
        
        # Simulate achievement conditions
        achievement_conditions = [
            {"arc": "academic", "type": "straight_a", "condition": "all_a_grades"},
            {"arc": "club", "type": "tournament_champion", "condition": "win_tournament"},
            {"arc": "romance", "type": "true_love", "condition": "max_relationship"}
        ]
        
        for condition in achievement_conditions:
            self.player_data = self.arc_manager.check_achievement_conditions(
                self.player_data, condition
            )
        
        # Verify achievement unlocking
        for arc_id in ["academic", "club", "romance"]:
            self.assertGreater(
                len(self.player_data["achievements"][arc_id]["unlocked"]),
                0,
                f"No achievements unlocked for {arc_id}"
            )
            self.assertLess(
                len(self.player_data["achievements"][arc_id]["locked"]),
                len(self.player_data["achievements"][arc_id]["unlocked"]),
                f"All achievements should not be locked for {arc_id}"
            )

if __name__ == '__main__':
    unittest.main() 