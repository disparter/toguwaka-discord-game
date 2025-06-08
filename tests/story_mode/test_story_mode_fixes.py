import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import Chapter

class TestStoryModeChapterSuffixes(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()

    def test_chapter_suffix_handling(self):
        """Test that chapter suffixes are handled correctly"""
        with patch('story_mode.progress.Progress.get_current_chapter') as mock_get_chapter:
            # Test chapter with suffix
            chapter = Chapter(
                chapter_id="chapter_1_a",
                title="Chapter 1A",
                content="Test content",
                choices=[]
            )
            mock_get_chapter.return_value = chapter
            
            current_chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertEqual(current_chapter.chapter_id, "chapter_1_a")

class TestStoryModeClubSpecificDialogues(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()

    def test_club_specific_content(self):
        """Test that club-specific content is handled correctly"""
        with patch('story_mode.progress.Progress.get_current_chapter') as mock_get_chapter, \
             patch('story_mode.progress.Progress.get_player_club') as mock_get_club:
            mock_get_club.return_value = "kendo"
            
            chapter = Chapter(
                chapter_id="club_event",
                title="Club Event",
                content="Test content",
                choices=[],
                club_specific_content={
                    "kendo": "Kendo club specific content",
                    "default": "Default content"
                }
            )
            mock_get_chapter.return_value = chapter
            
            current_chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertIn("kendo", current_chapter.club_specific_content)

class TestStoryModeConditionalChapterNavigation(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()

    def test_conditional_navigation(self):
        """Test that conditional chapter navigation works correctly"""
        with patch('story_mode.progress.Progress.get_current_chapter') as mock_get_chapter, \
             patch('story_mode.progress.Progress.get_player_stats') as mock_get_stats:
            mock_get_stats.return_value = {"strength": 15}
            
            chapter = Chapter(
                chapter_id="conditional_chapter",
                title="Conditional Chapter",
                content="Test content",
                choices=[
                    {
                        "text": "Strong path",
                        "next_chapter": "strong_path",
                        "condition": {"stat": "strength", "value": 10, "operator": ">="}
                    },
                    {
                        "text": "Weak path",
                        "next_chapter": "weak_path",
                        "condition": {"stat": "strength", "value": 10, "operator": "<"}
                    }
                ]
            )
            mock_get_chapter.return_value = chapter
            
            current_chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            available_choices = self.story_mode.get_available_choices(self.mock_ctx)
            self.assertEqual(len(available_choices), 1)
            self.assertEqual(available_choices[0]["next_chapter"], "strong_path")

class TestStoryModeChallengeChapterIDs(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()

    def test_challenge_chapter_handling(self):
        """Test that challenge chapter IDs are handled correctly"""
        with patch('story_mode.progress.Progress.get_current_chapter') as mock_get_chapter:
            chapter = Chapter(
                chapter_id="challenge_1",
                title="Challenge Chapter",
                content="Test content",
                choices=[],
                challenge_id="challenge_1"
            )
            mock_get_chapter.return_value = chapter
            
            current_chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertEqual(current_chapter.challenge_id, "challenge_1")

if __name__ == '__main__':
    unittest.main() 