import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_event_loading')

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the StoryMode class
from story_mode.story_mode import StoryMode

def test_event_loading():
    """Test that events are correctly loaded from the event_templates.json file."""
    logger.info("Initializing StoryMode...")
    story_mode = StoryMode()
    
    # Check if events were loaded
    event_count = len(story_mode.event_manager.events)
    logger.info(f"Loaded {event_count} events")
    
    # Print the first few events to verify they were loaded correctly
    for i, (event_id, event) in enumerate(list(story_mode.event_manager.events.items())[:3]):
        logger.info(f"Event {i+1}: {event_id} - {event.get_name()}")
    
    return event_count > 0

if __name__ == '__main__':
    success = test_event_loading()
    if success:
        logger.info("Test passed: Events were loaded successfully")
        sys.exit(0)
    else:
        logger.error("Test failed: No events were loaded")
        sys.exit(1)