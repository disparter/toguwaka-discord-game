#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n$1\n"
}

# Check if Python is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 >/dev/null 2>&1; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "pyvenv11" ]; then
    print_section "Creating virtual environment"
    python3 -m venv pyvenv11
fi

# Activate virtual environment
print_section "Activating virtual environment"
source pyvenv11/bin/activate

# Install test dependencies
print_section "Installing test dependencies"
pip install -r requirements-test.txt

# Install project dependencies
print_section "Installing project dependencies"
pip install -r requirements.txt

# Run tests
print_section "Running tests"
python -m pytest

# Store the exit code
TEST_EXIT_CODE=$?

# Check if tests passed
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed successfully!${NC}"
else
    echo -e "\n${RED}Some tests failed.${NC}"
fi

# Deactivate virtual environment
deactivate

# Exit with the test status
exit $TEST_EXIT_CODE 