import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from utils.game_mechanics.events import RandomEvent, TrainingEvent
from unittest.mock import patch

class TestRandomEvent(unittest.TestCase):
    def test_random_event_creation(self):
        """Testa a criação de um evento aleatório"""
        event = RandomEvent.create_random_event()
        self.assertIsInstance(event, RandomEvent)
        self.assertIsNotNone(event.get_title())
        self.assertIsNotNone(event.get_description())
        self.assertIsNotNone(event.get_type())
    
    def test_random_event_trigger(self):
        """Testa o trigger de um evento aleatório"""
        player = {
            "strength": 10,
            "agility": 10,
            "intelligence": 10,
            "hp": 100,
            "max_hp": 100,
            "experience": 0,
            "level": 1
        }
        event = RandomEvent.create_random_event()
        result = event.trigger(player)
        self.assertIsInstance(result, dict)
        self.assertIn("message", result)
        self.assertIn("effects", result)

class TestTrainingEvent(unittest.TestCase):
    def setUp(self):
        """Setup para os testes de treinamento"""
        self.player = {
            "strength": 10,
            "agility": 10,
            "intelligence": 10,
            "hp": 100,
            "max_hp": 100,
            "experience": 0,
            "level": 1
        }
    
    def test_training_event_creation(self):
        """Testa a criação de um evento de treinamento"""
        event = TrainingEvent.create_random_training_event()
        self.assertIsInstance(event, TrainingEvent)
        self.assertIsNotNone(event.get_title())
        self.assertIsNotNone(event.get_description())
        self.assertIsNotNone(event.get_type())
        self.assertIn("exp", event.get_effect())
        self.assertIn("attribute", event.get_effect())
    
    def test_training_event_trigger(self):
        """Testa o trigger de um evento de treinamento"""
        event = TrainingEvent.create_random_training_event()
        result = event.trigger(self.player)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exp_gain", result)
        self.assertIn("attribute_gain", result)
        self.assertIn("attribute_value", result)

if __name__ == '__main__':
    unittest.main() 