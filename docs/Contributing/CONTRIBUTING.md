# Contributing to Tokugawa Academy

Thank you for your interest in contributing to Tokugawa Academy! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in the [issue tracker](https://github.com/yourusername/tokugawa-discord-game/issues)
- Use the bug report template when creating a new issue
- Include detailed steps to reproduce the bug
- Include Python version and environment details
- Specify your OS and Discord version

### Suggesting Features

- Check if the feature has already been suggested in the [issue tracker](https://github.com/yourusername/tokugawa-discord-game/issues)
- Use the feature request template when creating a new issue
- Provide a clear description of the feature
- Explain why this feature would be useful
- Include any mockups or examples if applicable

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Set up your development environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
4. Make your changes
5. Run tests: `pytest`
6. Run linter: `flake8`
7. Format code: `black .`
8. Update documentation if necessary
9. Submit a pull request

### Development Setup

1. Clone the repository
2. Create and activate virtual environment
3. Install dependencies
4. Set up pre-commit hooks
5. Run tests to ensure everything is working

See [Getting Started](Development/getting-started.md) for detailed setup instructions.

## Style Guide

- Follow PEP 8
- Use meaningful variable and function names
- Write clear docstrings
- Keep functions small and focused
- Write tests for new features
- Use type hints

## Documentation

- Update documentation when adding new features
- Use clear and concise language
- Include examples where appropriate
- Keep documentation up to date
- Follow Google style for docstrings

## Commit Messages

- Use clear and descriptive commit messages
- Reference issue numbers when applicable
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")

## Review Process

1. All pull requests require at least one review
2. CI tests must pass
3. Documentation must be updated
4. Code must follow style guidelines
5. Type hints must be provided
6. Tests must be included

## Questions?

Feel free to ask questions in our [Discord server](https://discord.gg/your-invite-link) or open an issue. 