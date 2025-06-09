import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
import unittest
from src.utils.game_mechanics.events.random_event import RandomEvent

class TestRandomEvent(unittest.TestCase):
    def setUp(self):
        self.random_event = RandomEvent.create_random_event()

    def test_random_event_creation(self):
        """Test that a random event can be created"""
        self.assertIsInstance(self.random_event, RandomEvent)
        self.assertIsNotNone(self.random_event.get_title())
        self.assertIsNotNone(self.random_event.get_description())
        self.assertIsNotNone(self.random_event.get_type())

    def test_random_event_trigger(self):
        """Test that a random event can be triggered"""
        # Create a mock player as a dict with required attributes
        mock_player = {
            'strength': 10,
            'agility': 10,
            'intelligence': 10,
            'hp': 100,
            'max_hp': 100,
            'experience': 0,
            'level': 1
        }
        result = self.random_event.trigger(mock_player)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('message', result)
        self.assertIn('effects', result)

    def test_random_event_get_random_event(self):
        """Test that get_random_event returns a valid event template"""
        template = RandomEvent.get_random_event()
        self.assertIsInstance(template, dict)
        self.assertIn('title', template)
        self.assertIn('description', template)
        self.assertIn('type', template)
        self.assertIn('effects', template)

if __name__ == '__main__':
    unittest.main() 