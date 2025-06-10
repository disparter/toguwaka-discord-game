#!/bin/bash
# Script to run the Tokugawa Discord Bot

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Run the bot
echo "Starting Tokugawa Discord Bot..."
python bot.py

# Deactivate virtual environment
if [ -d "venv" ]; then
    deactivate
fi
