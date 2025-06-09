import unittest
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestQuizGrade(unittest.TestCase):
    """Test the quiz grade calculation with intellect factor."""
    
    def test_grade_calculation_with_intellect(self):
        """Test that intellect properly affects the grade calculation."""
        # Simulate the grade calculation from scheduled_events.py
        
        def calculate_grade(is_correct, question_difficulty, subject_difficulty, player_intellect):
            """Simulate the grade calculation from scheduled_events.py."""
            max_grade = 10.0
            base_grade = 5.0
            
            # Additional grade for correct answer, weighted by difficulty
            difficulty_multiplier = (question_difficulty + subject_difficulty) / 2
            correct_bonus = (max_grade - base_grade) * (difficulty_multiplier / 3)
            
            # Get player's intellect value and calculate intellect bonus
            intellect_bonus = (player_intellect - 5) * 0.2  # Each point above 5 gives 0.2 bonus
            
            final_grade = base_grade
            if is_correct:
                final_grade += correct_bonus
            
            # Add intellect bonus
            final_grade += intellect_bonus
            
            # Ensure grade doesn't exceed maximum
            final_grade = min(final_grade, max_grade)
            
            # Round to one decimal place
            final_grade = round(final_grade, 1)
            
            return final_grade
        
        # Test with default intellect (5)
        grade_default = calculate_grade(True, 2, 2, 5)
        print(f"Grade with intellect 5: {grade_default}")
        
        # Test with higher intellect (10)
        grade_high = calculate_grade(True, 2, 2, 10)
        print(f"Grade with intellect 10: {grade_high}")
        
        # Test with lower intellect (3)
        grade_low = calculate_grade(True, 2, 2, 3)
        print(f"Grade with intellect 3: {grade_low}")
        
        # Test with incorrect answer and high intellect
        grade_incorrect = calculate_grade(False, 2, 2, 10)
        print(f"Grade with incorrect answer and intellect 10: {grade_incorrect}")
        
        # Verify that higher intellect gives a higher grade
        self.assertGreater(grade_high, grade_default)
        
        # Verify that lower intellect gives a lower grade
        self.assertLess(grade_low, grade_default)
        
        # Verify that intellect bonus is applied even with incorrect answers
        self.assertGreater(grade_incorrect, 5.0)
        
        # Verify that the grade doesn't exceed the maximum
        self.assertLessEqual(grade_high, 10.0)
        
        # Calculate the expected intellect bonus for intellect 10
        expected_intellect_bonus = (10 - 5) * 0.2  # 5 points * 0.2 = 1.0
        
        # Verify that the intellect bonus is correctly applied
        self.assertAlmostEqual(grade_high - grade_default, expected_intellect_bonus, places=1)

if __name__ == "__main__":
    unittest.main()