import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from utils.game_mechanics.duel import DuelCalculator, DuelNarrator
from unittest.mock import patch

class TestDuelCalculator(unittest.TestCase):
    def setUp(self):
        """Setup para os testes de duelo"""
        self.challenger = {
            "user_id": 1,
            "name": "Challenger",
            "level": 10,
            "exp": 1000,
            "tusd": 500,
            "dexterity": 20,
            "intellect": 15,
            "charisma": 10,
            "power_stat": 30,
            "hp": 100,
            "max_hp": 100
        }
        
        self.opponent = {
            "user_id": 2,
            "name": "Opponent",
            "level": 8,
            "exp": 800,
            "tusd": 400,
            "dexterity": 18,
            "intellect": 12,
            "charisma": 8,
            "power_stat": 25,
            "hp": 90,
            "max_hp": 90
        }
    
    @patch('random.random', return_value=0.8)
    def test_calculate_outcome_physical(self, mock_random):
        """Testa o cálculo de resultado de um duelo físico"""
        calculator = DuelCalculator()
        result = calculator.calculate_outcome(self.challenger, self.opponent, duel_type="physical")
        
        # Verifica apenas a estrutura do resultado
        self.assertIsInstance(result["winner"], str)
        self.assertIsInstance(result["loser"], str)
        self.assertEqual(result["duel_type"], "physical")
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)
    
    @patch('random.random', return_value=0.8)
    def test_calculate_outcome_magical(self, mock_random):
        """Testa o cálculo de resultado de um duelo mágico"""
        calculator = DuelCalculator()
        result = calculator.calculate_outcome(self.challenger, self.opponent, duel_type="magical")
        
        # Verifica apenas a estrutura do resultado
        self.assertIsInstance(result["winner"], str)
        self.assertIsInstance(result["loser"], str)
        self.assertEqual(result["duel_type"], "magical")
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)

class TestDuelNarrator(unittest.TestCase):
    def setUp(self):
        """Setup para os testes de narração de duelo"""
        self.duel_result = {
            "winner": "Challenger",
            "loser": "Opponent",
            "duel_type": "physical",
            "win_margin": 10,
            "exp_reward": 100,
            "tusd_reward": 50
        }
    
    def test_narrate_duel(self):
        """Testa a narração de um duelo"""
        narrator = DuelNarrator()
        narration = narrator.generate_narration(self.duel_result)
        
        # Verifica apenas a estrutura da narração
        self.assertIsInstance(narration, str)
        self.assertIn(self.duel_result["winner"], narration)
        self.assertIn(self.duel_result["loser"], narration)
        self.assertIn(str(self.duel_result["exp_reward"]), narration)
        self.assertIn(str(self.duel_result["tusd_reward"]), narration)

if __name__ == '__main__':
    unittest.main() 