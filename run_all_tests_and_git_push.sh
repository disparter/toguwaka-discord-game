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

# Check if git is installed
if ! command_exists git; then
    echo -e "${RED}Error: git is not installed${NC}"
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

# Install/upgrade pip
print_section "Upgrading pip"
pip install --upgrade pip

# Install test dependencies
print_section "Installing test dependencies"
pip install -r requirements-test.txt

# Install project dependencies
print_section "Installing project dependencies"
pip install -r requirements.txt

# Create a directory for test outputs if it doesn't exist
mkdir -p test_outputs

# Run tests with coverage and save output to file
print_section "Running tests with coverage"
chmod +x run_tests.sh
./run_tests.sh > test_outputs/test_results.txt 2>&1

# Store the exit code
TEST_EXIT_CODE=$?

# Check if tests passed
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed successfully!${NC}"
    TEST_STATUS="passed"
else
    echo -e "\n${YELLOW}Some tests failed, but continuing with the process.${NC}"
    echo -e "${YELLOW}Test output saved to test_outputs/test_results.txt${NC}"
    TEST_STATUS="failed"
fi

# Print coverage summary
print_section "Coverage Summary"
coverage report | tee test_outputs/coverage_report.txt

# Open coverage report in browser if possible
if command_exists open; then
    open htmlcov/index.html
elif command_exists xdg-open; then
    xdg-open htmlcov/index.html
fi

# Git operations
print_section "Committing and pushing to Git"
git add .
if [ "$TEST_STATUS" = "passed" ]; then
    git commit -m "✅ All tests passed – build verified and coverage updated"
else
    git commit -m "⚠️ Some tests failed – committing anyway as requested"
fi
git push

# Generate prompt for test error analysis
if [ "$TEST_STATUS" = "failed" ]; then
    print_section "Test Error Analysis Prompt"
    echo -e "The following prompt can be used with an AI assistant to analyze and fix the test errors:"
    echo -e "${GREEN}------- COPY FROM HERE -------${NC}"
    echo "I'm working on a Python project and some tests are failing. Please help me analyze the test errors and suggest fixes. Here's the test output:"
    echo ""
    echo "\`\`\`"
    cat test_outputs/test_results.txt
    echo "\`\`\`"
    echo ""
    echo "And here's the coverage report:"
    echo ""
    echo "\`\`\`"
    cat test_outputs/coverage_report.txt
    echo "\`\`\`"
    echo ""
    echo "Please analyze these errors in depth and suggest specific fixes for each failing test. Include code examples where appropriate."
    echo -e "${GREEN}------- COPY TO HERE -------${NC}"
fi

# Deactivate virtual environment
deactivate
