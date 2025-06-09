# Test Suite for Academia Tokugawa

This directory contains the test suite for the Academia Tokugawa Discord game. The tests are organized by functionality and follow pytest conventions.

## Directory Structure

```
tests/
├── story/           # Story mode and narrative tests
├── commands/        # Command handler tests
├── services/        # Core service tests
├── persistence/     # Database and persistence tests
└── utils/          # Utility function tests
```

## Test Coverage

### Story Mode Tests
- Narrative flow and branching
- Chapter progression
- Choice processing
- Story state management

### Command Tests
- Command validation
- Command execution
- Command cooldowns
- Command permissions

### Service Tests
- Game mechanics
- Combat system
- Experience calculation
- Item effects
- Club management

### Persistence Tests
- DynamoDB operations
- Data consistency
- Error handling
- Data migration

### Utility Tests
- Helper functions
- Calculators
- Formatters
- Validators

## Running Tests

To run all tests:
```bash
pytest
```

To run specific test categories:
```bash
pytest tests/story/      # Story mode tests
pytest tests/commands/   # Command tests
pytest tests/services/   # Service tests
pytest tests/persistence/ # Database tests
pytest tests/utils/      # Utility tests
```

## Test Guidelines

1. Use pytest fixtures for common setup
2. Follow AAA pattern (Arrange, Act, Assert)
3. Use descriptive test names
4. Mock external dependencies
5. Test edge cases and error conditions
6. Keep tests focused and atomic

## Removed Tests

The following types of tests were removed during refactoring:

1. Trivial getter/setter tests
2. Redundant test cases
3. Overly complex mocks
4. Coverage-only tests without real value

## TODO

- [ ] Add tests for romance system
- [ ] Add tests for club events
- [ ] Add tests for attribute effects
- [ ] Add tests for item combinations
- [ ] Add tests for achievement system
