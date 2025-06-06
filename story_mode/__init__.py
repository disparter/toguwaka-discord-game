"""
Academia Tokugawa - Story Mode System

This package contains the implementation of the story mode system for the Academia Tokugawa game,
following SOLID principles of software design.

The system is modular, extensible, and easy to maintain, encouraging interactive and responsive
narrative design.

Modules:
- interfaces: Defines interfaces for the main components of the system
- chapter: Implements the Chapter interface for different types of chapters
- event: Implements the Event interface for different types of events
- npc: Implements the NPC interface for different types of NPCs
- progress: Implements the StoryProgressManager interface for tracking player progress
- story_mode: Main class that coordinates all components

For more information, see the README.md file in this directory.
"""

from .interfaces import (
    Chapter, Event, NPC, ChapterLoader, EventManager, StoryProgressManager
)
from .chapter import (
    BaseChapter, StoryChapter, ChallengeChapter, BranchingChapter
)
from .event import (
    BaseEvent, ClimacticEvent, RandomEvent, SeasonalEvent, DefaultEventManager
)
from .npc import (
    BaseNPC, StudentNPC, FacultyNPC, NPCManager
)
from .progress import (
    DefaultStoryProgressManager
)
from .story_mode import (
    FileChapterLoader, StoryMode
)

__all__ = [
    # Interfaces
    'Chapter', 'Event', 'NPC', 'ChapterLoader', 'EventManager', 'StoryProgressManager',
    
    # Chapter implementations
    'BaseChapter', 'StoryChapter', 'ChallengeChapter', 'BranchingChapter',
    
    # Event implementations
    'BaseEvent', 'ClimacticEvent', 'RandomEvent', 'SeasonalEvent', 'DefaultEventManager',
    
    # NPC implementations
    'BaseNPC', 'StudentNPC', 'FacultyNPC', 'NPCManager',
    
    # Progress implementations
    'DefaultStoryProgressManager',
    
    # Story mode
    'FileChapterLoader', 'StoryMode'
]