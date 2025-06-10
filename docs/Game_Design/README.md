# Game Design Guide

## Overview

This guide covers the core game design and implementation details of Tokugawa Academy, including story structure, romance system, and club mechanics.

## Story System

### File Structure
```
data/story_mode/
├── main/chapters/           # Individual chapter files
└── assets/
    └── images/
        └── story/          # Story images
            ├── backgrounds/ # Background images
            ├── characters/  # Character images
            └── locations/   # Location images
```

### Chapter Structure
```json
{
  "id": "chapter_1_1",
  "title": "Chapter Title",
  "text": "Chapter text...",
  "background_image": "images/story/backgrounds/chapter_1_1.png",
  "character_images": {
    "npc_1": "images/story/characters/npc_1/normal.png",
    "npc_2": "images/story/characters/npc_2/happy.jpg"
  },
  "location_image": "images/story/locations/classroom.jpg",
  "choices": [
    {
      "text": "Choice 1",
      "next_chapter": "chapter_1_2",
      "effects": {
        "reputation": {
          "fire_club": 10
        }
      }
    }
  ],
  "skill_checks": [
    {
      "skill": "intelligence",
      "difficulty": 5,
      "success_chapter": "chapter_1_2",
      "failure_chapter": "chapter_1_3"
    }
  ],
  "club_progression": {
    "fire_club": 1
  },
  "romance_route": {
    "character": "npc_1",
    "points": 5
  }
}
```

## Romance System

### File Structure
```
data/story_mode/
├── npcs/
│   ├── npc_1.json
│   ├── npc_2.json
│   └── ...
├── romance/
│   ├── routes/
│   │   ├── route_1.json
│   │   ├── route_2.json
│   │   └── ...
│   └── events/
│       ├── event_1.json
│       ├── event_2.json
│       └── ...
└── assets/
    └── images/
        └── characters/
            ├── npc_1/
            │   ├── normal.jpg
            │   ├── happy.jpg
            │   └── ...
            └── ...
```

### Relationship Levels
1. **Acquaintances** (0-19 points)
   - Basic interactions
   - Initial dialogues
   - Introduction events

2. **Friends** (20-39 points)
   - More interactions available
   - Friendship events
   - Shop discounts

3. **Close** (40-59 points)
   - Special events
   - Initial romantic scenes
   - Exclusive benefits

4. **Romantic** (60-79 points)
   - Romantic events
   - Special scenes
   - Unique rewards

5. **Committed** (80-100 points)
   - Final events
   - Multiple endings
   - Maximum rewards

## Club System

### File Structure
```
data/story_mode/
├── clubs/
│   ├── fire_club.json
│   ├── elementalists.json
│   └── ...
└── reputation/
    ├── club_reputation.json
    └── reputation_items.json
```

### Club Phases
1. **Introduction**
   - Club and member introduction
   - Specific mechanics tutorial
   - Initial missions
   - Initial rewards

2. **Crisis**
   - Club conflict or challenge
   - Significant choices
   - Reputation impact
   - Skill development

3. **Resolution**
   - Crisis resolution
   - Choice consequences
   - Special rewards
   - New opportunities

4. **Final**
   - Club story conclusion
   - Final rewards
   - Game impact
   - Club legacy

### Reputation Levels
1. **Neutral** (0-20)
   - Basic club access
   - Limited interactions

2. **Respected** (21-40)
   - Special event access
   - Shop discounts
   - New interactions

3. **Valued** (41-60)
   - Exclusive mission access
   - Special benefits
   - Decision influence

4. **Leader** (61-80)
   - Full functionality access
   - Decision power
   - Exclusive rewards

5. **Legend** (81-100)
   - Maximum status
   - Unique benefits
   - Club legacy

## Integration

### Story Integration
- Club-specific chapters
- Romance route chapters
- Special events
- Choice consequences

### System Integration
- Reputation affects choices
- Romance affects club events
- Club membership affects story
- Image system integration

## Best Practices

### Story
1. No dead ends
2. Regular checkpoints
3. Visual fallback system
4. Choice consistency

### Romance
1. Varied interactions
2. Natural progression
3. Meaningful choices
4. Clear feedback

### Clubs
1. Balanced rewards
2. Clear progression
3. Varied activities
4. System integration

## Writing Guidelines

### Style
- Consistent tone
- Character voice
- Japanese cultural elements
- School life atmosphere

### Content
- Age-appropriate content
- Cultural sensitivity
- Character consistency
- Story coherence

## Game Mechanics

### Time System
- Real-time progression
- Scheduled events
- Time-based activities
- Daily routines

### Interaction System
- Command-based interactions
- Character responses
- Event triggers
- Choice consequences

### Progression System
- Experience points
- Relationship levels
- Skill development
- Story progression

## Event System

### Types of Events
- Story events
- Character events
- Club events
- Special occasions

### Event Triggers
- Time-based
- Relationship-based
- Story-based
- Random events

## Implementation Notes

### Story Files
- JSON-based story structure
- Event definitions
- Character data
- Location data

### Game State
- Player progress
- Character states
- Relationship data
- Inventory system 