# Getting Started with Development

This guide will help you set up your development environment for Tokugawa Academy.

## Prerequisites

- Python 3.8 or higher
- pip
- Git
- Discord Bot Token (requires Discord Developer Account)
- Docker (optional, for local DynamoDB)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tokugawa-discord-game.git
cd tokugawa-discord-game
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
DISCORD_TOKEN=your_discord_bot_token
PYTHON_ENV=development
```

## Database Options

### Option 1: AWS DynamoDB (Recommended for Production)
- Create an AWS account
- Set up DynamoDB in AWS Console
- Add AWS credentials to `.env`:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

### Option 2: Local DynamoDB with Docker
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```
Then add to `.env`:
```env
DYNAMODB_ENDPOINT=http://localhost:8000
```

### Option 3: LocalStack (Alternative Local Development)
```bash
docker run -p 4566:4566 localstack/localstack
```
Then add to `.env`:
```env
DYNAMODB_ENDPOINT=http://localhost:4566
```

### Option 4: SQLite (Simple Local Development)
Add to `.env`:
```env
DB_TYPE=sqlite
DB_PATH=./data/game.db
```

## Development Workflow

1. Start the development server:
```bash
python bot.py
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
flake8
```

## Project Structure

```
tokugawa-discord-game/
├── src/
│   ├── commands/      # Discord bot commands
│   ├── events/        # Discord event handlers
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── tests/             # Test files
├── docs/              # Documentation
└── config/            # Configuration files
```

## Available Scripts

- `python bot.py` - Start development server
- `pytest` - Run tests
- `flake8` - Run linter
- `black .` - Format code
- `python setup_db.py` - Set up database tables

## Debugging

1. Enable debug logs by setting `DEBUG=tokugawa:*` in your `.env` file
2. Use the debugger in your IDE
3. Check the logs in the console

## Common Issues

### Bot Not Responding
- Check if the bot token is correct
- Verify the bot has proper permissions
- Check if the bot is online
- Ensure your Discord Developer account is properly set up

### Database Connection Issues
- For AWS DynamoDB: Check AWS credentials and region
- For Local DynamoDB: Ensure Docker container is running
- For SQLite: Check file permissions and path

## Next Steps

- Read the [Architecture Documentation](Architecture/README.md)
- Review the [Contributing Guidelines](Contributing/CONTRIBUTING.md)

## Need Help?

- Join our [Discord server](https://discord.gg/your-invite-link)
- Open an [issue](https://github.com/yourusername/tokugawa-discord-game/issues)
- Check the [FAQ](Guides/FAQ.md) 