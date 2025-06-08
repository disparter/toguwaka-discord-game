import unittest
import os
import sys
import re
import subprocess
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGitOperations(unittest.TestCase):
    """
    Test class for Git operations and commit message validation.
    
    These tests validate Git operations and commit messages against the best practices
    outlined in git_commit_best_practices.md.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Path to the git_commit_best_practices.md file
        self.best_practices_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'git_commit_best_practices.md'
        )
        
        # Test commit messages
        self.valid_commit_messages = [
            "fix(auth): Prevent timing attack in password verification",
            "feat(ui): Add dark mode toggle to user settings",
            "docs(readme): Update installation instructions",
            "refactor(database): Optimize query performance",
            "test(api): Add tests for new endpoints"
        ]
        
        self.invalid_commit_messages = [
            "fixed a bug",  # Not imperative mood, no scope
            "Added new feature and fixed some bugs",  # Not imperative mood, multiple changes
            "fix bug in authentication system with a very long subject line that exceeds the recommended limit",  # Too long
            "feat: add feature.",  # Ends with period
            "DOCS: update readme"  # Not capitalized correctly
        ]
    
    def test_git_executable_exists(self):
        """Test that the git executable exists and is accessible."""
        try:
            result = subprocess.run(
                ['git', '--version'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            self.assertIn('git version', result.stdout)
        except (subprocess.SubprocessError, FileNotFoundError):
            self.skipTest("Git executable not found or not accessible")
    
    def test_git_commit_best_practices_file_exists(self):
        """Test that the git_commit_best_practices.md file exists."""
        self.assertTrue(os.path.exists(self.best_practices_path))
    
    def test_validate_commit_message_subject(self):
        """Test validation of commit message subject line."""
        # Define regex patterns based on best practices
        subject_pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\([a-z0-9-]+\))?: [A-Z].{1,48}[^.]$'
        
        # Test valid commit messages
        for message in self.valid_commit_messages:
            subject = message.split('\n')[0]
            self.assertTrue(
                re.match(subject_pattern, subject),
                f"Valid commit message failed validation: {subject}"
            )
        
        # Test invalid commit messages
        for message in self.invalid_commit_messages:
            subject = message.split('\n')[0]
            self.assertFalse(
                re.match(subject_pattern, subject),
                f"Invalid commit message passed validation: {subject}"
            )
    
    @patch('subprocess.run')
    def test_git_commit_with_valid_message(self, mock_run):
        """Test git commit with a valid commit message."""
        # Set up the mock
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[main 1234abc] feat(ui): Add dark mode toggle\n 1 file changed, 10 insertions(+), 2 deletions(-)",
            stderr=""
        )
        
        # Call git commit with a valid message
        result = subprocess.run(
            ['git', 'commit', '-m', 'feat(ui): Add dark mode toggle'],
            capture_output=True,
            text=True
        )
        
        # Verify the result
        self.assertEqual(result.returncode, 0)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_git_commit_with_invalid_message(self, mock_run):
        """Test git commit with an invalid commit message."""
        # In a real environment, this would be enforced by a pre-commit hook
        # Here we're just simulating the validation
        
        # Set up the mock
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Commit message does not follow the convention"
        )
        
        # Call git commit with an invalid message
        result = subprocess.run(
            ['git', 'commit', '-m', 'fixed a bug'],
            capture_output=True,
            text=True
        )
        
        # Verify the result
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error: Commit message does not follow the convention", result.stderr)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_git_commit_with_issue_reference(self, mock_run):
        """Test git commit with a reference to an issue."""
        # Set up the mock
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[main 1234abc] feat(ui): Add dark mode toggle\n 1 file changed, 10 insertions(+), 2 deletions(-)",
            stderr=""
        )
        
        commit_message = 'feat(ui): Add dark mode toggle\n\nCloses #123'
        # Call git commit with a valid message that references an issue
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            text=True
        )
        
        # Verify the result
        self.assertEqual(result.returncode, 0)
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        self.assertIn(commit_message, args[0])
    
    @patch('subprocess.run')
    def test_git_commit_with_multiple_changes(self, mock_run):
        """Test git commit with multiple changes in the body."""
        # Set up the mock
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[main 1234abc] feat(ui): Add dark mode toggle\n 3 files changed, 25 insertions(+), 5 deletions(-)",
            stderr=""
        )
        
        commit_message = 'feat(ui): Add dark mode toggle\n\n- Added toggle switch component\n- Implemented theme switching logic\n- Added local storage persistence'
        # Call git commit with a valid message that includes multiple changes
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            text=True
        )
        
        # Verify the result
        self.assertEqual(result.returncode, 0)
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        self.assertIn(commit_message, args[0])

if __name__ == '__main__':
    unittest.main() 