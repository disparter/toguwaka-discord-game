import unittest
from unittest.mock import patch
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from utils.game_mechanics.events.training_event import TrainingEvent
from utils.game_mechanics.constants import TRAINING_OUTCOMES

class TestTrainingEvent(unittest.TestCase):
    """Test cases for the TrainingEvent class."""

    def test_init(self):
        """Test that the event is initialized correctly."""
        title = "Test Training"
        description = "Test description"
        exp_gain = 20
        attribute_gain = "dexterity"

        event = TrainingEvent(title, description, exp_gain, attribute_gain)

        self.assertEqual(event.get_title(), title)
        self.assertEqual(event.get_description(), description)
        self.assertEqual(event.get_type(), "training")
        self.assertEqual(event.get_effect(), {"exp": exp_gain, "attribute": attribute_gain})

    def test_trigger(self):
        """Test that the event correctly triggers and returns a result."""
        title = "Test Training"
        description = "Test description"
        exp_gain = 20
        attribute_gain = "dexterity"

        event = TrainingEvent(title, description, exp_gain, attribute_gain)

        # Create a mock player
        player = {
            "name": "Test Player",
            "level": 1,
            "exp": 0,
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
        self.assertEqual(result["exp_gain"], exp_gain)
        self.assertEqual(result["attribute_gain"], attribute_gain)

    @patch('random.choice')
    @patch('random.randint')
    def test_create_random_training_event(self, mock_randint, mock_choice):
        """Test that the event correctly creates a random training event."""
        # Mock the random choices
        mock_choice.side_effect = [
            "You trained intensely and felt your power grow!",  # Description
            "intellect"  # Attribute gain
        ]
        # Mock the random integer
        mock_randint.return_value = 15  # Exp gain (mocked to be deterministic)

        # Create a random event
        event = TrainingEvent.create_random_training_event()

        # Check the event
        self.assertEqual(event.get_title(), "Treinamento Concluído")
        self.assertEqual(event.get_description(), "You trained intensely and felt your power grow!")
        self.assertEqual(event.get_type(), "training")
        self.assertEqual(event.get_effect(), {"exp": 15, "attribute": "intellect"})

    def test_get_random_outcome(self):
        """Test that the event correctly returns a random training outcome."""
        outcome = TrainingEvent.get_random_outcome()
        self.assertIn(outcome, TRAINING_OUTCOMES)

if __name__ == '__main__':
    unittest.main()
