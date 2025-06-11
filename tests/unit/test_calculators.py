import unittest
import sys
import os
from decimal import Decimal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from utils.game_mechanics.calculators import ExperienceCalculator, HPFactorCalculator

class TestExperienceCalculator(unittest.TestCase):
    def test_calculate_required_exp(self):
        """Testa o cálculo de experiência necessária para o próximo nível"""
        calculator = ExperienceCalculator()
        exp = calculator.calculate_required_exp(1)
        self.assertEqual(exp, 100)
        
        exp = calculator.calculate_required_exp(2)
        self.assertEqual(exp, 400)
        
        exp = calculator.calculate_required_exp(3)
        self.assertEqual(exp, 900)

class TestHPFactorCalculator(unittest.TestCase):
    def setUp(self):
        """Setup para os testes de fator de HP"""
        self.calculator = HPFactorCalculator()
    
    def test_calculate_factor_above_threshold(self):
        """Testa o cálculo do fator quando HP está acima do threshold"""
        factor = self.calculator.calculate_factor(Decimal('80'), Decimal('100'))
        self.assertEqual(factor, Decimal('0.9'))
    
    def test_calculate_factor_below_threshold(self):
        """Testa o cálculo do fator quando HP está abaixo do threshold"""
        factor = self.calculator.calculate_factor(Decimal('30'), Decimal('100'))
        self.assertEqual(factor, Decimal('0.79'))  # 0.7 + (0.3 * 0.3)
    
    def test_calculate_factor_full_hp(self):
        """Testa o cálculo do fator quando HP está cheio"""
        factor = self.calculator.calculate_factor(Decimal('100'), Decimal('100'))
        self.assertEqual(factor, Decimal('1.0'))

if __name__ == '__main__':
    unittest.main() 