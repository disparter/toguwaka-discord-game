#!/bin/bash
# Script to run the Tokugawa Discord Bot

# Activate virtual environment if it exists
if [ -d "venvpy11" ]; then
    echo "Activating virtual environment..."
    source venvpy11/bin/activate

    # Install required packages
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Run the bot for 10 seconds, then kill it (for testing)
echo "Starting Tokugawa Discord Bot for 10 seconds..."
python src/bot.py &
BOT_PID=$!
sleep 100
echo "Stopping Tokugawa Discord Bot (PID $BOT_PID) after 10 seconds."
kill $BOT_PID

# Deactivate virtual environment
if [ -d "venvpy11" ]; then
    deactivate
fi
