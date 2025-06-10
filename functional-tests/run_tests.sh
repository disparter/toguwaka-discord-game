#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to handle script termination
cleanup() {
    echo -e "\n${GREEN}Cleaning up...${NC}"
    docker-compose down
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Create reports directory if it doesn't exist
mkdir -p reports

# Create volume directory for LocalStack if it doesn't exist
mkdir -p volume

# Export the test channel
export TOKUGAWA_CHANNEL=tokugawa-bot-tests

# Start services using docker-compose
echo -e "${GREEN}Starting test environment...${NC}"
docker-compose up --build --abort-on-container-exit

# Check if tests were successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Tests completed successfully!${NC}"
    echo "Reports generated in the 'reports' directory:"
    echo "- HTML Coverage Report: reports/coverage/index.html"
    echo "- JUnit XML Report: reports/junit.xml"
    echo "- HTML Test Report: reports/report.html"
else
    echo -e "${RED}Tests failed!${NC}"
fi

# Cleanup
cleanup 