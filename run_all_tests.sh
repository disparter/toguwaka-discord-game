#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}\n"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if pip is installed
if ! command_exists pip3; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_section "Creating virtual environment"
    python3 -m venv venv
fi

# Activate virtual environment
print_section "Activating virtual environment"
source venv/bin/activate

# Install/upgrade pip
print_section "Upgrading pip"
pip install --upgrade pip

# Install test dependencies
print_section "Installing test dependencies"
pip install -r requirements-test.txt

# Install project dependencies
print_section "Installing project dependencies"
pip install -r requirements.txt

# Run tests with coverage
print_section "Running tests with coverage"
pytest --cov=. --cov-report=term-missing --cov-report=html

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed successfully!${NC}"
    
    # Print coverage summary
    print_section "Coverage Summary"
    coverage report
    
    # Open coverage report in browser if possible
    if command_exists open; then
        open htmlcov/index.html
    elif command_exists xdg-open; then
        xdg-open htmlcov/index.html
    fi
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate 