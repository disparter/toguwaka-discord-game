import logging
import sys

# Set up logging to capture warnings
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('tokugawa_bot')

# Import the StoryMode class
from story_mode.story_mode import StoryMode

# Create a StoryMode instance
story_mode = StoryMode()

# Check if the mystery_chapter.json file is loaded
chapter = story_mode.chapter_loader.load_chapter("mystery_chapter")
if chapter:
    print("Successfully loaded mystery_chapter without warnings!")
    print(f"Chapter title: {chapter.get_title()}")
    print(f"Chapter has choices: {hasattr(chapter, 'choices')}")
    if hasattr(chapter, 'choices'):
        print(f"Number of choices: {len(chapter.choices)}")
else:
    print("Failed to load mystery_chapter!")