# import unittest
# import sys
# import os
# from decimal import Decimal
# from unittest.mock import patch, MagicMock

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
# from utils.game_mechanics.duel import DuelCalculator, DuelNarrator

# class TestDuelCalculator(unittest.TestCase):
#     def setUp(self):
#         """Setup para os testes de duelo"""
#         self.challenger = {
#             "user_id": 1,
#             "name": "Challenger",
#             "level": Decimal('10'),
#             "exp": Decimal('1000'),
#             "tusd": Decimal('500'),
#             "dexterity": Decimal('20'),
#             "intellect": Decimal('15'),
#             "charisma": Decimal('10'),
#             "power_stat": Decimal('30'),
#             "hp": Decimal('100'),
#             "max_hp": Decimal('100')
#         }
        
#         self.opponent = {
#             "user_id": 2,
#             "name": "Opponent",
#             "level": Decimal('8'),
#             "exp": Decimal('800'),
#             "tusd": Decimal('400'),
#             "dexterity": Decimal('18'),
#             "intellect": Decimal('12'),
#             "charisma": Decimal('8'),
#             "power_stat": Decimal('25'),
#             "hp": Decimal('90'),
#             "max_hp": Decimal('90')
#         }

#         # Mock the weights to use Decimal
#         self.weights_patch = patch.object(DuelCalculator, 'ATTRIBUTE_WEIGHTS', {
#             "physical": {
#                 "dexterity": Decimal('0.6'),
#                 "power_stat": Decimal('0.3'),
#                 "intellect": Decimal('0.05'),
#                 "charisma": Decimal('0.05')
#             },
#             "magical": {
#                 "power_stat": Decimal('0.5'),
#                 "intellect": Decimal('0.3'),
#                 "dexterity": Decimal('0.1'),
#                 "charisma": Decimal('0.1')
#             }
#         })
#         self.weights_patch.start()
    
#     def tearDown(self):
#         """Cleanup after tests"""
#         self.weights_patch.stop()
    
#     @patch('random.uniform', return_value=Decimal('1.0'))
#     def test_calculate_outcome_physical(self, mock_uniform):
#         """Testa o cálculo de resultado de um duelo físico"""
#         calculator = DuelCalculator()
#         result = calculator.calculate_outcome(self.challenger, self.opponent, duel_type="physical")
        
#         # Verifica apenas a estrutura do resultado
#         self.assertIsInstance(result["winner"], str)
#         self.assertIsInstance(result["loser"], str)
#         self.assertEqual(result["duel_type"], "physical")
#         self.assertGreater(result["win_margin"], 0)
#         self.assertGreater(result["exp_reward"], 0)
#         self.assertGreater(result["tusd_reward"], 0)
#         self.assertGreater(result["hp_loss"], 0)
    
#     @patch('random.uniform', return_value=Decimal('1.0'))
#     def test_calculate_outcome_magical(self, mock_uniform):
#         """Testa o cálculo de resultado de um duelo mágico"""
#         calculator = DuelCalculator()
#         result = calculator.calculate_outcome(self.challenger, self.opponent, duel_type="magical")
        
#         # Verifica apenas a estrutura do resultado
#         self.assertIsInstance(result["winner"], str)
#         self.assertIsInstance(result["loser"], str)
#         self.assertEqual(result["duel_type"], "magical")
#         self.assertGreater(result["win_margin"], 0)
#         self.assertGreater(result["exp_reward"], 0)
#         self.assertGreater(result["tusd_reward"], 0)
#         self.assertGreater(result["hp_loss"], 0)

# class TestDuelNarrator(unittest.TestCase):
#     def setUp(self):
#         """Setup para os testes de narração de duelo"""
#         self.duel_result = {
#             "winner": "Challenger",
#             "loser": "Opponent",
#             "duel_type": "physical",
#             "win_margin": Decimal('10'),
#             "exp_reward": Decimal('100'),
#             "tusd_reward": Decimal('50')
#         }
    
#     def test_narrate_duel(self):
#         """Testa a narração de um duelo"""
#         narrator = DuelNarrator()
#         narration = narrator.generate_narration(self.duel_result)
        
#         # Verifica apenas a estrutura da narração
#         self.assertIsInstance(narration, str)
#         self.assertIn(self.duel_result["winner"], narration)
#         self.assertIn(self.duel_result["loser"], narration)
#         self.assertIn(str(self.duel_result["exp_reward"]), narration)
#         self.assertIn(str(self.duel_result["tusd_reward"]), narration)

# if __name__ == '__main__':
#     unittest.main() 