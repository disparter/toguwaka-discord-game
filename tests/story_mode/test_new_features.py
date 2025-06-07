import unittest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from story_mode.narrative_validator import NarrativePathValidator
from story_mode.club_system import ClubSystem
from story_mode.decision_dashboard import DecisionTracker

class TestNarrativeValidator(unittest.TestCase):
    """Test the narrative path validator functionality."""
    
    def setUp(self):
        # Create a temporary directory for test chapters
        self.test_dir = tempfile.mkdtemp()
        
        # Create test chapter files
        self.create_test_chapters()
        
        # Initialize the validator
        self.validator = NarrativePathValidator(self.test_dir)
        self.validator.load_chapters()
        
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
    def create_test_chapters(self):
        # Create a simple chapter structure for testing
        chapter1 = {
            "1_1": {
                "type": "story",
                "title": "Test Chapter 1",
                "description": "Test description",
                "dialogues": [
                    {"npc": "Test NPC", "text": "Test dialogue"}
                ],
                "choices": [
                    {"text": "Go to chapter 2", "next_chapter": "1_2", "metadata": {"var1": "value1"}},
                    {"text": "Stay in chapter 1", "next_dialogue": 2}
                ],
                "next_chapter": "1_2"
            }
        }
        
        chapter2 = {
            "1_2": {
                "type": "story",
                "title": "Test Chapter 2",
                "description": "Test description",
                "dialogues": [
                    {"npc": "Test NPC", "text": "Test dialogue"}
                ],
                "conditional_next_chapter": {
                    "var1": {
                        "value1": "1_3",
                        "default": "1_1"
                    }
                }
            }
        }
        
        chapter3 = {
            "1_3": {
                "type": "story",
                "title": "Test Chapter 3",
                "description": "Test description",
                "dialogues": [
                    {"npc": "Test NPC", "text": "Test dialogue"}
                ],
                "next_chapter": "1_1"  # Loop back to chapter 1
            }
        }
        
        # Write the chapters to files
        with open(os.path.join(self.test_dir, "chapter1.json"), 'w') as f:
            json.dump(chapter1, f)
            
        with open(os.path.join(self.test_dir, "chapter2.json"), 'w') as f:
            json.dump(chapter2, f)
            
        with open(os.path.join(self.test_dir, "chapter3.json"), 'w') as f:
            json.dump(chapter3, f)
            
    def test_chapter_loading(self):
        """Test that chapters are loaded correctly."""
        self.assertEqual(len(self.validator.chapters_data), 3)
        self.assertIn("1_1", self.validator.chapters_data)
        self.assertIn("1_2", self.validator.chapters_data)
        self.assertIn("1_3", self.validator.chapters_data)
        
    def test_path_validation(self):
        """Test that paths are validated correctly."""
        result = self.validator.validate_narrative_paths()
        self.assertTrue(result)
        
    def test_broken_reference_detection(self):
        """Test that broken references are detected."""
        # Add a broken reference
        self.validator.chapters_data["1_1"]["next_chapter"] = "non_existent"
        
        result = self.validator.validate_narrative_paths()
        self.assertFalse(result)
        self.assertIn("non_existent", self.validator.referenced_chapters - self.validator.defined_chapters)
        
    def test_variable_usage_validation(self):
        """Test that variable usage is validated."""
        # Add a variable usage without definition
        self.validator.chapters_data["1_2"]["conditional_next_chapter"]["undefined_var"] = {"value": "1_3"}
        
        result = self.validator.validate_narrative_paths()
        self.assertFalse(result)
        self.assertIn("undefined_var", [var for var in self.validator.variable_usages if var not in self.validator.variable_definitions])
        
    def test_path_coverage(self):
        """Test path coverage reporting."""
        self.validator.validate_narrative_paths()
        self.validator.simulate_path_coverage()
        
        report = self.validator.generate_coverage_report()
        self.assertEqual(report["total_chapters"], 3)
        self.assertTrue(report["total_paths"] > 0)
        self.assertTrue(report["covered_paths"] > 0)
        self.assertTrue(0 <= report["coverage_percentage"] <= 100)

class TestClubSystem(unittest.TestCase):
    """Test the club system functionality."""
    
    def setUp(self):
        # Initialize the club system
        self.club_system = ClubSystem()
        
        # Create a test player
        self.player_data = {
            "name": "Test Player",
            "level": 1,
            "experience": 0
        }
        
    def test_club_initialization(self):
        """Test that player club data is initialized correctly."""
        self.club_system.initialize_player_club_data(self.player_data)
        
        self.assertIn("club", self.player_data)
        self.assertIsNone(self.player_data["club"]["id"])
        self.assertEqual(self.player_data["club"]["rank"], 1)
        self.assertEqual(self.player_data["club"]["experience"], 0)
        
    def test_join_club(self):
        """Test joining a club."""
        result = self.club_system.join_club(self.player_data, 1)
        
        self.assertTrue(result)
        self.assertEqual(self.player_data["club"]["id"], 1)
        self.assertEqual(self.player_data["club"]["rank"], 1)
        self.assertEqual(len(self.player_data["club"]["pending_missions"]), 3)
        
    def test_club_experience(self):
        """Test adding club experience and ranking up."""
        self.club_system.join_club(self.player_data, 1)
        
        # Add enough experience to rank up
        result = self.club_system.add_club_experience(self.player_data, 150)
        
        self.assertEqual(result["rank"], 2)
        self.assertTrue(result.get("rank_up", False))
        self.assertEqual(self.player_data["club"]["rank"], 2)
        
    def test_club_missions(self):
        """Test club missions."""
        self.club_system.join_club(self.player_data, 1)
        
        # Get initial missions
        initial_missions = len(self.player_data["club"]["pending_missions"])
        self.assertEqual(initial_missions, 3)
        
        # Complete a mission
        mission_id = self.player_data["club"]["pending_missions"][0]["id"]
        result = self.club_system.complete_mission(self.player_data, mission_id)
        
        self.assertEqual(len(self.player_data["club"]["pending_missions"]), initial_missions)  # Should generate a new one
        self.assertEqual(len(self.player_data["club"]["completed_missions"]), 1)
        self.assertEqual(self.player_data["club"]["missions_completed"], 1)
        
    def test_club_competitions(self):
        """Test club competitions."""
        self.club_system.join_club(self.player_data, 1)
        
        # Rank up to be able to create competitions
        self.club_system.add_club_experience(self.player_data, 300)
        self.assertEqual(self.player_data["club"]["rank"], 3)
        
        # Create a competition
        competition = self.club_system.create_club_competition(self.player_data, 2)
        
        self.assertEqual(competition["host_club_id"], 1)
        self.assertEqual(competition["opponent_club_id"], 2)
        self.assertEqual(competition["status"], "scheduled")
        
        # Resolve the competition
        result = self.club_system.resolve_competition(self.player_data, competition["id"], True)
        
        self.assertEqual(result["outcome"], "victory")
        self.assertTrue(result["experience_gained"] > 0)
        
    def test_rivalries_and_alliances(self):
        """Test rivalries and alliances."""
        self.club_system.join_club(self.player_data, 1)
        
        # Rank up to be able to form alliances and rivalries
        self.club_system.add_club_experience(self.player_data, 700)
        self.assertEqual(self.player_data["club"]["rank"], 4)
        
        # Form an alliance
        alliance = self.club_system.form_alliance(self.player_data, 4)
        
        self.assertEqual(alliance["club_id"], 4)
        self.assertTrue(alliance["is_new"])
        self.assertIn("4", self.player_data["club"]["alliances"])
        
        # Declare a rivalry
        rivalry = self.club_system.declare_rivalry(self.player_data, 2)
        
        self.assertEqual(rivalry["club_id"], 2)
        self.assertTrue(rivalry["is_new"])
        self.assertIn("2", self.player_data["club"]["rivalries"])

class TestDecisionDashboard(unittest.TestCase):
    """Test the decision dashboard functionality."""
    
    def setUp(self):
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize the decision tracker
        self.decision_tracker = DecisionTracker(self.test_dir)
        
        # Create a test player
        self.player_data = {
            "name": "Test Player",
            "level": 1,
            "experience": 0,
            "club": {
                "id": 1,
                "rank": 2
            }
        }
        
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_record_player_choice(self):
        """Test recording player choices."""
        result = self.decision_tracker.record_player_choice(
            self.player_data,
            "1_1",
            "choice_1",
            "Test choice"
        )
        
        self.assertTrue(result)
        self.assertIn("choice_history", self.player_data)
        self.assertIn("1_1", self.player_data["choice_history"])
        self.assertIn("choice_1", self.player_data["choice_history"]["1_1"])
        self.assertEqual(self.player_data["choice_history"]["1_1"]["choice_1"]["text"], "Test choice")
        
    def test_community_comparison(self):
        """Test community choice comparison."""
        # Record a choice
        self.decision_tracker.record_player_choice(
            self.player_data,
            "1_1",
            "choice_1",
            "Test choice"
        )
        
        # Get comparison
        comparison = self.decision_tracker.get_community_comparison(
            self.player_data,
            "1_1",
            "choice_1"
        )
        
        self.assertEqual(comparison["player_choice"], "Test choice")
        self.assertIn("Test choice", comparison["community_choices"])
        self.assertEqual(comparison["total_choices"], 1)
        self.assertEqual(comparison["player_percentage"], 100.0)
        
    def test_ethical_reflection(self):
        """Test ethical reflection generation."""
        # Get a club-specific reflection
        reflection = self.decision_tracker.get_ethical_reflection(
            self.player_data,
            "club",
            "1"
        )
        
        self.assertEqual(reflection["category"], "club")
        self.assertEqual(reflection["id"], "1")
        self.assertTrue(len(reflection["reflections"]) > 0)
        
        # Get a general reflection
        reflection = self.decision_tracker.get_ethical_reflection(
            self.player_data,
            "power"
        )
        
        self.assertEqual(reflection["category"], "power")
        self.assertTrue(len(reflection["reflections"]) > 0)
        
    def test_alternative_paths(self):
        """Test alternative paths functionality."""
        # Record multiple choices for the same decision point
        self.decision_tracker.record_player_choice(
            self.player_data,
            "1_1",
            "choice_1",
            "Player choice"
        )
        
        # Create a second player to make a different choice
        player2_data = {"name": "Player 2"}
        self.decision_tracker.record_player_choice(
            player2_data,
            "1_1",
            "choice_1",
            "Alternative choice"
        )
        
        # Get alternative paths
        alternatives = self.decision_tracker.get_alternative_paths(
            self.player_data,
            "1_1"
        )
        
        self.assertEqual(alternatives["chapter_id"], "1_1")
        self.assertEqual(len(alternatives["alternative_paths"]), 1)
        self.assertEqual(alternatives["alternative_paths"][0]["player_choice"], "Player choice")
        self.assertEqual(alternatives["alternative_paths"][0]["alternatives"][0]["text"], "Alternative choice")
        
    def test_dashboard_generation(self):
        """Test comprehensive dashboard generation."""
        # Record some choices
        self.decision_tracker.record_player_choice(
            self.player_data,
            "1_1",
            "choice_1",
            "I want to learn more about this power."
        )
        
        self.decision_tracker.record_player_choice(
            self.player_data,
            "1_2",
            "choice_1",
            "I'll help you with this task."
        )
        
        # Generate dashboard
        dashboard = self.decision_tracker.generate_dashboard(self.player_data)
        
        self.assertIn("personality", dashboard)
        self.assertIn("ethical_reflection", dashboard)
        self.assertIn("recent_comparisons", dashboard)
        self.assertIn("alternative_paths", dashboard)
        self.assertEqual(dashboard["total_choices_made"], 2)
        self.assertEqual(dashboard["chapters_completed"], 2)

if __name__ == '__main__':
    unittest.main()