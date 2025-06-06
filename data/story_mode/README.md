# Content Management System for Tokugawa Discord Game

This directory contains the narrative content and tools for managing the story mode of the Tokugawa Discord Game. The content management system provides tools for creating, validating, and analyzing narrative content.

## Directory Structure

- `chapters/`: Contains JSON files with chapter data
- `events/`: Contains JSON files with event data
- `npcs/`: Contains JSON files with NPC data
- `narrative_templates/`: Contains template files for different types of narrative content
- `schemas/`: Contains JSON schema files for validating content

## Templates

The `narrative_templates` directory contains templates for different types of narrative content:

- `chapters.json`: Templates for different types of chapters (story, branching, challenge)
- `choices.json`: Templates for different types of choices based on player attributes
- `dialogues.json`: Templates for different types of dialogues based on NPCs and contexts
- `outcomes.json`: Templates for different types of outcomes based on player choices
- `sequences.json`: Templates for narrative sequences (linear, branching, conditional)
- `character_arcs.json`: Templates for character development arcs (player, NPC, club)
- `quests.json`: Templates for different types of quests (main, side, daily, challenge)

## Schemas

The `schemas` directory contains JSON schema files for validating content:

- `chapter_schema.json`: Schema for validating chapter data
- `event_schema.json`: Schema for validating event data
- `npc_schema.json`: Schema for validating NPC data
- `sequence_schema.json`: Schema for validating narrative sequences
- `character_arc_schema.json`: Schema for validating character arcs
- `quest_schema.json`: Schema for validating quests

## Tools

The content management system includes several command-line tools for working with narrative content:

### Content Generator

The content generator helps create new narrative content based on templates.

```bash
python -m utils.content_generator --list
python -m utils.content_generator --template chapters.story_chapter --output data/story_mode/chapters/new_chapter.json --id new_chapter_1
```

Options:
- `--list`: List available templates
- `--template`: Template to use (format: template_type.template_name)
- `--output`: Output file path
- `--id`: ID for the generated content
- `--non-interactive`: Generate content without prompting for input

### Content Validator

The content validator helps validate narrative content against schemas.

```bash
python -m utils.content_validator --list
python -m utils.content_validator --file data/story_mode/chapters/chapter_1.json --schema chapter
python -m utils.content_validator --directory data/story_mode/chapters --schema chapter
```

Options:
- `--list`: List available schemas
- `--file`: JSON file to validate
- `--schema`: Schema to validate against
- `--directory`: Directory containing JSON files to validate
- `--fix`: Attempt to fix validation errors

### Content Analyzer

The content analyzer helps analyze player choices and identify narrative bottlenecks.

```bash
python -m utils.content_analyzer --export data/story_mode/analytics.json
python -m utils.content_analyzer --heatmap choice_heatmap.png
python -m utils.content_analyzer --progression progression_chart.png
python -m utils.content_analyzer --bottlenecks
```

Options:
- `--export`: Export analytics data to a JSON file
- `--heatmap`: Generate a choice heatmap and save to the specified file
- `--progression`: Generate a progression chart and save to the specified file
- `--bottlenecks`: Identify narrative bottlenecks

## Creating New Content

To create new narrative content:

1. Choose a template that matches the type of content you want to create
2. Use the content generator to create a new content file based on the template
3. Edit the generated file to customize the content
4. Use the content validator to ensure that the content is valid
5. Add the content to the appropriate directory

Example workflow for creating a new chapter:

```bash
# List available templates
python -m utils.content_generator --list

# Generate a new chapter based on the story_chapter template
python -m utils.content_generator --template chapters.story_chapter --output data/story_mode/chapters/new_chapter.json --id new_chapter_1

# Validate the new chapter
python -m utils.content_validator --file data/story_mode/chapters/new_chapter.json --schema chapter
```

## Analyzing Player Choices

To analyze player choices and identify narrative bottlenecks:

```bash
# Export analytics data
python -m utils.content_analyzer --export data/story_mode/analytics.json

# Generate visualizations
python -m utils.content_analyzer --heatmap choice_heatmap.png
python -m utils.content_analyzer --progression progression_chart.png

# Identify bottlenecks
python -m utils.content_analyzer --bottlenecks
```

The analytics data can help identify:
- Which chapters are most/least completed
- Which choices are most/least popular
- Which events are most/least participated in
- How players are progressing through the story
- Where players tend to drop off (bottlenecks)

## Best Practices

- Use templates as a starting point for new content
- Validate content against schemas to ensure consistency
- Use descriptive IDs for content (e.g., "chapter_1_1" for Chapter 1.1)
- Keep content files organized by type (chapters, events, NPCs)
- Use the content analyzer to identify and fix narrative bottlenecks
- Test new content with a small group of players before releasing it to everyone
- Document any custom content types or extensions to the system

## Extending the System

To extend the content management system:

1. Create new templates for new types of content
2. Create new schemas for validating the new content types
3. Update the content generator, validator, and analyzer to support the new content types
4. Add tests for the new functionality
5. Document the new content types and tools

## Troubleshooting

- If the content generator fails, check that the template exists and is valid
- If the content validator reports errors, fix the issues in the content file and validate again
- If the content analyzer fails, check that the player data file exists and is valid
- If visualization features are not available, install matplotlib, numpy, and seaborn