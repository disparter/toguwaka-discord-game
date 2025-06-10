# Development Guide

## Overview

This guide covers the essential aspects of developing Tokugawa Academy, a Discord-based roleplaying game.

## Project Structure

```
tokugawa-discord-game/
├── src/
│   ├── commands/      # Discord bot commands
│   ├── events/        # Discord event handlers
│   ├── models/        # Game state models
│   ├── services/      # Game logic
│   └── utils/         # Utility functions
├── tests/             # Test files
└── docs/              # Documentation
```

## Core Systems

### Story System
- Branching narrative structure
- Event-driven story progression
- Character interaction system
- Save/load game state

### Character System
- Character state management
- Relationship tracking
- Inventory system
- Stats and progression

### Command System
- Discord command handling
- Input validation
- Response formatting
- Error handling

## Development Guidelines

### Code Style
- Follow PEP 8
- Use meaningful variable names
- Write clear comments
- Keep functions focused and small

### Testing
- Unit tests with pytest
- Integration tests for commands
- Mock Discord API for testing
- Test coverage requirements

### Git Workflow
- Feature branches
- Pull request reviews
- Semantic versioning
- Conventional commits

## Getting Started

See [Getting Started Guide](getting-started.md) for detailed setup instructions.

## Common Tasks

### Adding New Commands
1. Create command file in `src/commands`
2. Implement command logic
3. Add tests
4. Update documentation

### Modifying Story Content
1. Update story files
2. Test story branches
3. Verify character interactions
4. Update documentation

### Adding New Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## Troubleshooting

### Common Issues
- Command not responding
- Story progression issues
- State management problems
- Testing failures

### Debugging
- Use debug logs
- Check Discord permissions
- Verify game state
- Test in isolation

## Support

For development issues:
1. Check existing issues
2. Ask in Discord
3. Create new issue if needed 