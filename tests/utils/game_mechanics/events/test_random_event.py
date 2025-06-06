import unittest
from unittest.mock import patch, mock_open
import sys
import os
import json

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from utils.game_mechanics.events.random_event import RandomEvent, load_events_from_json
from utils.game_mechanics.constants import RANDOM_EVENTS

class TestRandomEvent(unittest.TestCase):
    """Test cases for the RandomEvent class."""

    def test_init(self):
        """Test that the event is initialized correctly."""
        title = "Test Event"
        description = "Test description"
        event_type = "positive"
        effect = {"exp": 50, "tusd": 20}

        event = RandomEvent(title, description, event_type, effect)

        self.assertEqual(event.get_title(), title)
        self.assertEqual(event.get_description(), description)
        self.assertEqual(event.get_type(), event_type)
        self.assertEqual(event.get_effect(), effect)

    def test_trigger_exp_change(self):
        """Test that the event correctly triggers and returns a result with exp change."""
        title = "Test Event"
        description = "Test description"
        event_type = "positive"
        effect = {"exp": 50}

        event = RandomEvent(title, description, event_type, effect)

        # Create a mock player
        player = {
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 5,
            "intellect": 5,
            "charisma": 5,
            "power_stat": 5
        }

        # Trigger the event
        result = event.trigger(player)

        # Check the result
        self.assertEqual(result["title"], title)
        self.assertEqual(result["description"], description)
        self.assertEqual(result["type"], event_type)
        self.assertEqual(result["exp_change"], 50)

    def test_trigger_tusd_change(self):
        """Test that the event correctly triggers and returns a result with tusd change."""
        title = "Test Event"
        description = "Test description"
        event_type = "negative"
        effect = {"tusd": -10}

        event = RandomEvent(title, description, event_type, effect)

        # Create a mock player
        player = {
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 5,
            "intellect": 5,
            "charisma": 5,
            "power_stat": 5
        }

        # Trigger the event
        result = event.trigger(player)

        # Check the result
        self.assertEqual(result["title"], title)
        self.assertEqual(result["description"], description)
        self.assertEqual(result["type"], event_type)
        self.assertEqual(result["tusd_change"], -10)

    def test_trigger_attribute_change(self):
        """Test that the event correctly triggers and returns a result with attribute change."""
        title = "Test Event"
        description = "Test description"
        event_type = "positive"
        effect = {"attribute": "intellect", "attribute_value": 2}

        event = RandomEvent(title, description, event_type, effect)

        # Create a mock player
        player = {
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 5,
            "intellect": 5,
            "charisma": 5,
            "power_stat": 5
        }

        # Trigger the event
        result = event.trigger(player)

        # Check the result
        self.assertEqual(result["title"], title)
        self.assertEqual(result["description"], description)
        self.assertEqual(result["type"], event_type)
        self.assertEqual(result["attribute_change"], "intellect")
        self.assertEqual(result["attribute_value"], 2)

    def test_trigger_random_attribute(self):
        """Test that the event correctly handles random attribute selection."""
        title = "Test Event"
        description = "Test description"
        event_type = "positive"
        effect = {"attribute": "random"}

        event = RandomEvent(title, description, event_type, effect)

        # Create a mock player
        player = {
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 5,
            "intellect": 5,
            "charisma": 5,
            "power_stat": 5
        }

        # Patch random.choice to return a deterministic attribute
        with patch('random.choice', return_value="dexterity"):
            # Trigger the event
            result = event.trigger(player)

            # Check the result
            self.assertEqual(result["attribute_change"], "dexterity")
            self.assertEqual(result["attribute_value"], 1)  # Default value

    @patch('random.choice')
    def test_create_from_template(self, mock_choice):
        """Test that the event correctly creates an event from a template."""
        # Create a template
        template = {
            "title": "Festival dos Poderes",
            "description": "Você foi convidado para o Festival dos Poderes!",
            "type": "positive",
            "effect": {"exp": 50, "tusd": 20}
        }

        # Create an event from the template
        event = RandomEvent.create_from_template(template)

        # Check the event
        self.assertEqual(event.get_title(), template["title"])
        self.assertEqual(event.get_description(), template["description"])
        self.assertEqual(event.get_type(), template["type"])
        self.assertEqual(event.get_effect(), template["effect"])

    @patch('random.choice')
    def test_get_random_event(self, mock_choice):
        """Test that the event correctly returns a random event template."""
        # Mock random.choice to return a deterministic event
        mock_choice.return_value = RANDOM_EVENTS[0]

        # Get a random event template
        template = RandomEvent.get_random_event()

        # Check the template
        self.assertEqual(template, RANDOM_EVENTS[0])

    @patch('utils.game_mechanics.events.random_event.RandomEvent.get_random_event')
    @patch('utils.game_mechanics.events.random_event.RandomEvent.create_from_template')
    def test_create_random_event(self, mock_create_from_template, mock_get_random_event):
        """Test that the event correctly creates a random event."""
        # Create a mock template and event
        template = {
            "title": "Festival dos Poderes",
            "description": "Você foi convidado para o Festival dos Poderes!",
            "type": "positive",
            "effect": {"exp": 50, "tusd": 20}
        }
        mock_event = RandomEvent(
            template["title"],
            template["description"],
            template["type"],
            template["effect"]
        )

        # Set up the mocks
        mock_get_random_event.return_value = template
        mock_create_from_template.return_value = mock_event

        # Create a random event
        event = RandomEvent.create_random_event()

        # Check that the mocks were called correctly
        mock_get_random_event.assert_called_once()
        mock_create_from_template.assert_called_once_with(template)

        # Check that the event is the mock event
        self.assertEqual(event, mock_event)

    def test_load_events_from_json_success(self):
        """Test that events are correctly loaded from a JSON file."""
        # Mock JSON data
        mock_events = [
            {
                "title": "Test Event 1",
                "description": "Test description 1",
                "type": "positive",
                "category": "test",
                "effect": {"exp": 50, "tusd": 20},
                "rarity": "common"
            },
            {
                "title": "Test Event 2",
                "description": "Test description 2",
                "type": "negative",
                "category": "test",
                "effect": {"exp": 30, "tusd": -10},
                "rarity": "rare"
            }
        ]

        # Mock the open function to return our mock JSON data
        mock_file = mock_open(read_data=json.dumps(mock_events))

        # Patch the open function and json.load
        with patch('builtins.open', mock_file):
            events = load_events_from_json('mock_path.json')

            # Check that the events were loaded correctly
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["title"], "Test Event 1")
            self.assertEqual(events[1]["title"], "Test Event 2")

    def test_load_events_from_json_file_not_found(self):
        """Test that an empty list is returned when the file is not found."""
        # Patch the open function to raise FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError):
            events = load_events_from_json('nonexistent_file.json')

            # Check that an empty list is returned
            self.assertEqual(events, [])

    def test_load_events_from_json_invalid_json(self):
        """Test that an empty list is returned when the JSON is invalid."""
        # Mock the open function to return invalid JSON
        mock_file = mock_open(read_data="invalid json")

        # Patch the open function
        with patch('builtins.open', mock_file):
            events = load_events_from_json('invalid_json.json')

            # Check that an empty list is returned
            self.assertEqual(events, [])

if __name__ == '__main__':
    unittest.main()
