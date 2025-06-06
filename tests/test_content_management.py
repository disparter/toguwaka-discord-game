import unittest
import os
import json
import tempfile
import shutil
from utils.content_generator import ContentGenerator
from utils.content_validator import ContentValidator
from utils.content_analyzer import ContentAnalyzer

class TestContentManagement(unittest.TestCase):
    """
    Test cases for the content management system.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Create temporary directories for test data
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        self.schemas_dir = os.path.join(self.temp_dir, "schemas")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.schemas_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create test templates
        self.create_test_templates()
        
        # Create test schemas
        self.create_test_schemas()
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        shutil.rmtree(self.temp_dir)
    
    def create_test_templates(self):
        """
        Create test template files.
        """
        # Create a simple chapter template
        chapters_template = {
            "test_chapter": {
                "type": "story",
                "title": "Test Chapter",
                "description": "A test chapter for unit testing",
                "dialogues": [
                    {"npc": "Test NPC", "text": "This is a test dialogue."}
                ],
                "choices": [
                    {"text": "Test choice", "next_dialogue": 1}
                ],
                "completion_exp": 100,
                "completion_tusd": 200,
                "next_chapter": "next_chapter_id"
            }
        }
        
        with open(os.path.join(self.templates_dir, "chapters.json"), 'w', encoding='utf-8') as f:
            json.dump(chapters_template, f, indent=2)
    
    def create_test_schemas(self):
        """
        Create test schema files.
        """
        # Create a simple chapter schema
        chapter_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Chapter Schema",
            "description": "Schema for validating chapter data in the story mode",
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["type", "title", "description"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["story", "branching", "challenge"]
                    },
                    "title": {
                        "type": "string",
                        "minLength": 1
                    },
                    "description": {
                        "type": "string",
                        "minLength": 1
                    },
                    "dialogues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["npc", "text"],
                            "properties": {
                                "npc": {
                                    "type": "string",
                                    "minLength": 1
                                },
                                "text": {
                                    "type": "string",
                                    "minLength": 1
                                }
                            }
                        }
                    },
                    "choices": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["text"],
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "minLength": 1
                                },
                                "next_dialogue": {
                                    "type": "integer",
                                    "minimum": 0
                                }
                            }
                        }
                    },
                    "completion_exp": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "completion_tusd": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "next_chapter": {
                        "type": "string"
                    }
                }
            }
        }
        
        with open(os.path.join(self.schemas_dir, "chapter_schema.json"), 'w', encoding='utf-8') as f:
            json.dump(chapter_schema, f, indent=2)
    
    def test_content_generator(self):
        """
        Test the ContentGenerator class.
        """
        generator = ContentGenerator(
            templates_dir=self.templates_dir,
            schemas_dir=self.schemas_dir,
            output_dir=self.output_dir
        )
        
        # Test listing templates
        templates = generator.list_templates()
        self.assertIn("chapters.test_chapter", templates)
        
        # Test generating content
        output_file = os.path.join(self.output_dir, "test_chapter.json")
        content = generator.generate_content(
            template_name="chapters.test_chapter",
            output_file=output_file,
            content_id="test_chapter_1",
            interactive=False  # Non-interactive mode for testing
        )
        
        # Check that the content was generated correctly
        self.assertEqual(content["type"], "story")
        self.assertEqual(content["title"], "Test Chapter")
        self.assertEqual(len(content["dialogues"]), 1)
        self.assertEqual(content["dialogues"][0]["npc"], "Test NPC")
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Check the content of the file
        with open(output_file, 'r', encoding='utf-8') as f:
            file_content = json.load(f)
        
        self.assertIn("test_chapter_1", file_content)
        self.assertEqual(file_content["test_chapter_1"]["type"], "story")
    
    def test_content_validator(self):
        """
        Test the ContentValidator class.
        """
        # Create a test chapter file
        test_chapter = {
            "test_chapter_1": {
                "type": "story",
                "title": "Test Chapter",
                "description": "A test chapter for unit testing",
                "dialogues": [
                    {"npc": "Test NPC", "text": "This is a test dialogue."}
                ],
                "choices": [
                    {"text": "Test choice", "next_dialogue": 1}
                ],
                "completion_exp": 100,
                "completion_tusd": 200,
                "next_chapter": "next_chapter_id"
            }
        }
        
        test_chapter_file = os.path.join(self.output_dir, "test_chapter.json")
        with open(test_chapter_file, 'w', encoding='utf-8') as f:
            json.dump(test_chapter, f, indent=2)
        
        validator = ContentValidator(schemas_dir=self.schemas_dir)
        
        # Test listing schemas
        schemas = validator.list_schemas()
        self.assertIn("chapter", schemas)
        
        # Test validating a file
        is_valid, errors = validator.validate_file(test_chapter_file, "chapter")
        self.assertTrue(is_valid, f"Validation failed with errors: {errors}")
        
        # Test validating content directly
        is_valid, errors = validator.validate_content(test_chapter, "chapter")
        self.assertTrue(is_valid, f"Validation failed with errors: {errors}")
        
        # Test validating invalid content
        invalid_chapter = {
            "invalid_chapter": {
                "type": "invalid_type",  # Invalid type
                "title": "",  # Empty title
                "description": "A test chapter for unit testing"
            }
        }
        
        is_valid, errors = validator.validate_content(invalid_chapter, "chapter")
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
    
    def test_content_analyzer(self):
        """
        Test the ContentAnalyzer class.
        """
        # Create test player data
        player_data = {
            "player1": {
                "level": 5,
                "story_progress": {
                    "completed_chapters": ["1_1", "1_2", "1_3"],
                    "choices": {
                        "1_1": {"choice_1": 0, "choice_2": 1},
                        "1_2": {"choice_1": 2}
                    },
                    "completed_events": ["event1", "event2"],
                    "hierarchy_tier": 2,
                    "character_relationships": {
                        "NPC1": 50,
                        "NPC2": 30
                    }
                }
            },
            "player2": {
                "level": 3,
                "story_progress": {
                    "completed_chapters": ["1_1", "1_2"],
                    "choices": {
                        "1_1": {"choice_1": 1, "choice_2": 0},
                        "1_2": {"choice_1": 1}
                    },
                    "completed_events": ["event1"],
                    "hierarchy_tier": 1,
                    "character_relationships": {
                        "NPC1": 20,
                        "NPC2": 40
                    }
                }
            }
        }
        
        player_data_file = os.path.join(self.output_dir, "player_data.json")
        with open(player_data_file, 'w', encoding='utf-8') as f:
            json.dump(player_data, f, indent=2)
        
        analyzer = ContentAnalyzer(data_dir=self.output_dir)
        
        # Test analyzing player choices
        results = analyzer.analyze_player_choices()
        
        # Check chapter completion
        self.assertEqual(results["chapter_completion"]["1_1"], 2)
        self.assertEqual(results["chapter_completion"]["1_2"], 2)
        self.assertEqual(results["chapter_completion"]["1_3"], 1)
        
        # Check choice distribution
        self.assertEqual(results["choice_distribution"]["1_1"]["choice_1"], 1)
        self.assertEqual(results["choice_distribution"]["1_1"]["choice_2"], 1)
        self.assertEqual(results["choice_distribution"]["1_2"]["choice_1"], 3)
        
        # Check event participation
        self.assertEqual(results["event_participation"]["event1"], 2)
        self.assertEqual(results["event_participation"]["event2"], 1)
        
        # Check player progression
        self.assertEqual(results["player_progression"]["levels"]["3"], 1)
        self.assertEqual(results["player_progression"]["levels"]["5"], 1)
        self.assertEqual(results["player_progression"]["hierarchy_tiers"]["1"], 1)
        self.assertEqual(results["player_progression"]["hierarchy_tiers"]["2"], 1)
        
        # Check relationship affinities
        self.assertEqual(len(results["relationship_affinities"]["NPC1"]), 2)
        self.assertEqual(len(results["relationship_affinities"]["NPC2"]), 2)
        
        # Test identifying bottlenecks
        bottlenecks = analyzer.identify_bottlenecks()
        self.assertEqual(len(bottlenecks), 1)
        self.assertEqual(bottlenecks[0]["chapter_id"], "1_3")
        
        # Test exporting analytics
        analytics_file = os.path.join(self.output_dir, "analytics.json")
        analyzer.export_analytics(analytics_file)
        self.assertTrue(os.path.exists(analytics_file))
        
        # Check the content of the analytics file
        with open(analytics_file, 'r', encoding='utf-8') as f:
            analytics = json.load(f)
        
        self.assertIn("player_choices", analytics)
        self.assertIn("bottlenecks", analytics)
        self.assertIn("visualization_available", analytics)

if __name__ == "__main__":
    unittest.main()