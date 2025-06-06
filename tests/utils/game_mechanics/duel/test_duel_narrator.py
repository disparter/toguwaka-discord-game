import unittest
from unittest.mock import patch
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from utils.game_mechanics.duel.duel_narrator import DuelNarrator

class TestDuelNarrator(unittest.TestCase):
    """Test cases for the DuelNarrator class."""

    def setUp(self):
        """Set up test data."""
        # Create a mock duel result
        self.duel_result = {
            "winner": {
                "name": "Challenger",
                "level": 5,
                "exp": 1000,
                "tusd": 500
            },
            "loser": {
                "name": "Opponent",
                "level": 5,
                "exp": 1000,
                "tusd": 500
            },
            "duel_type": "physical",
            "win_margin": 15,
            "exp_reward": 50,
            "tusd_reward": 20
        }

    @patch('random.choice')
    def test_generate_narration_physical(self, mock_choice):
        """Test that the narrator correctly generates narrations for physical duels."""
        # Mock the random choices to make the test deterministic
        mock_choice.side_effect = [
            "{winner_name} e {loser_name} começaram uma batalha física intensa!",  # Intro
            "{winner_name} e {loser_name} estavam muito equilibrados, mas no final a vitória pendeu para um lado.",  # Middle
            "No final, {winner_name} emergiu vitorioso, conquistando {exp_reward} de experiência e {tusd_reward} TUSD!"  # Conclusion
        ]

        # Generate narration
        narration = DuelNarrator.generate_narration(self.duel_result)

        # Check the narration
        expected_narration = (
            "Challenger e Opponent começaram uma batalha física intensa!\n\n"
            "Challenger e Opponent estavam muito equilibrados, mas no final a vitória pendeu para um lado.\n\n"
            "No final, Challenger emergiu vitorioso, conquistando 50 de experiência e 20 TUSD!"
        )
        self.assertEqual(narration, expected_narration)

    @patch('random.choice')
    def test_generate_narration_mental(self, mock_choice):
        """Test that the narrator correctly generates narrations for mental duels."""
        # Update duel type
        self.duel_result["duel_type"] = "mental"

        # Mock the random choices to make the test deterministic
        mock_choice.side_effect = [
            "Um duelo de mentes brilhantes entre {winner_name} e {loser_name} teve início!",  # Intro
            "{winner_name} demonstrou clara superioridade durante todo o duelo.",  # Middle
            "A vitória foi de {winner_name}, que ganhou {exp_reward} de experiência e {tusd_reward} TUSD pelo seu desempenho!"  # Conclusion
        ]

        # Generate narration
        narration = DuelNarrator.generate_narration(self.duel_result)

        # Check the narration
        expected_narration = (
            "Um duelo de mentes brilhantes entre Challenger e Opponent teve início!\n\n"
            "Challenger demonstrou clara superioridade durante todo o duelo.\n\n"
            "A vitória foi de Challenger, que ganhou 50 de experiência e 20 TUSD pelo seu desempenho!"
        )
        self.assertEqual(narration, expected_narration)

    @patch('random.choice')
    def test_generate_narration_strategic(self, mock_choice):
        """Test that the narrator correctly generates narrations for strategic duels."""
        # Update duel type
        self.duel_result["duel_type"] = "strategic"

        # Mock the random choices to make the test deterministic
        mock_choice.side_effect = [
            "Um jogo de estratégia e tática começou entre {winner_name} e {loser_name}!",  # Intro
            "{winner_name} e {loser_name} estavam muito equilibrados, mas no final a vitória pendeu para um lado.",  # Middle
            "No final, {winner_name} emergiu vitorioso, conquistando {exp_reward} de experiência e {tusd_reward} TUSD!"  # Conclusion
        ]

        # Generate narration
        narration = DuelNarrator.generate_narration(self.duel_result)

        # Check the narration
        expected_narration = (
            "Um jogo de estratégia e tática começou entre Challenger e Opponent!\n\n"
            "Challenger e Opponent estavam muito equilibrados, mas no final a vitória pendeu para um lado.\n\n"
            "No final, Challenger emergiu vitorioso, conquistando 50 de experiência e 20 TUSD!"
        )
        self.assertEqual(narration, expected_narration)

    @patch('random.choice')
    def test_generate_narration_social(self, mock_choice):
        """Test that the narrator correctly generates narrations for social duels."""
        # Update duel type
        self.duel_result["duel_type"] = "social"

        # Mock the random choices to make the test deterministic
        mock_choice.side_effect = [
            "O debate entre {winner_name} e {loser_name} atraiu uma multidão de espectadores!",  # Intro
            "{winner_name} demonstrou clara superioridade durante todo o duelo.",  # Middle
            "A vitória foi de {winner_name}, que ganhou {exp_reward} de experiência e {tusd_reward} TUSD pelo seu desempenho!"  # Conclusion
        ]

        # Generate narration
        narration = DuelNarrator.generate_narration(self.duel_result)

        # Check the narration
        expected_narration = (
            "O debate entre Challenger e Opponent atraiu uma multidão de espectadores!\n\n"
            "Challenger demonstrou clara superioridade durante todo o duelo.\n\n"
            "A vitória foi de Challenger, que ganhou 50 de experiência e 20 TUSD pelo seu desempenho!"
        )
        self.assertEqual(narration, expected_narration)

    @patch('random.choice')
    def test_generate_narration_high_margin(self, mock_choice):
        """Test that the narrator correctly generates narrations for high margin duels."""
        # Update win margin
        self.duel_result["win_margin"] = 30

        # Mock the random choices to make the test deterministic
        mock_choice.side_effect = [
            "{winner_name} e {loser_name} começaram uma batalha física intensa!",  # Intro
            "{winner_name} demonstrou clara superioridade durante todo o duelo.",  # Middle
            "No final, {winner_name} emergiu vitorioso, conquistando {exp_reward} de experiência e {tusd_reward} TUSD!"  # Conclusion
        ]

        # Generate narration
        narration = DuelNarrator.generate_narration(self.duel_result)

        # Check the narration
        expected_narration = (
            "Challenger e Opponent começaram uma batalha física intensa!\n\n"
            "Challenger demonstrou clara superioridade durante todo o duelo.\n\n"
            "No final, Challenger emergiu vitorioso, conquistando 50 de experiência e 20 TUSD!"
        )
        self.assertEqual(narration, expected_narration)

    @patch('random.choice')
    def test_generate_narration_invalid_type(self, mock_choice):
        """Test that the narrator handles invalid duel types gracefully."""
        # Update duel type
        self.duel_result["duel_type"] = "invalid"

        # Mock the random choices to make the test deterministic
        mock_choice.side_effect = [
            "{winner_name} e {loser_name} começaram uma batalha física intensa!",  # Intro (should default to physical)
            "{winner_name} e {loser_name} estavam muito equilibrados, mas no final a vitória pendeu para um lado.",  # Middle
            "No final, {winner_name} emergiu vitorioso, conquistando {exp_reward} de experiência e {tusd_reward} TUSD!"  # Conclusion
        ]

        # Generate narration
        narration = DuelNarrator.generate_narration(self.duel_result)

        # Check the narration
        expected_narration = (
            "Challenger e Opponent começaram uma batalha física intensa!\n\n"
            "Challenger e Opponent estavam muito equilibrados, mas no final a vitória pendeu para um lado.\n\n"
            "No final, Challenger emergiu vitorioso, conquistando 50 de experiência e 20 TUSD!"
        )
        self.assertEqual(narration, expected_narration)

if __name__ == '__main__':
    unittest.main()
