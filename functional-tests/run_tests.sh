#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to handle script termination
cleanup() {
    echo -e "\n${GREEN}Cleaning up...${NC}"
    if [ ! -z "$LOCALSTACK_CONTAINER" ]; then
        docker stop $LOCALSTACK_CONTAINER
        echo "Stopped LocalStack container"
    fi
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Create reports directory if it doesn't exist
mkdir -p reports

# Start LocalStack
echo -e "${GREEN}Starting LocalStack...${NC}"
LOCALSTACK_CONTAINER=$(docker run -d \
    -p 4566:4566 \
    -p 4571:4571 \
    -e SERVICES=dynamodb,s3,cloudwatch \
    -e DEBUG=1 \
    -e DATA_DIR=/tmp/localstack/data \
    localstack/localstack)

echo "LocalStack container ID: $LOCALSTACK_CONTAINER"

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 10

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade pip
python -m pip install --upgrade pip

# Install requirements
echo -e "${GREEN}Installing requirements...${NC}"
pip install -r requirements.txt

# Run tests with coverage and generate HTML report
echo -e "${GREEN}Running tests...${NC}"
pytest \
    --cov=. \
    --cov-report=html:reports/coverage \
    --cov-report=term-missing \
    --junitxml=reports/junit.xml \
    --html=reports/report.html \
    --self-contained-html

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