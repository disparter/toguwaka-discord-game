# Functional Tests for Tokugawa Discord Game

This directory contains functional tests for the Tokugawa Discord Game, implemented using pytest-bdd and LocalStack for AWS service simulation.

## Prerequisites

- Python 3.8+
- Docker
- LocalStack

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start LocalStack:
```bash
docker run --rm -it -p 4566:4566 -p 4571:4571 localstack/localstack
```

## Running Tests

To run all tests:
```bash
pytest
```

To run specific test files:
```bash
pytest features/player_registration.feature
pytest features/inventory_management.feature
```

To run tests with coverage:
```bash
pytest --cov=.
```

## Test Structure

- `features/`: Contains Gherkin feature files
- `steps/`: Contains step definitions for the features
- `conftest.py`: Contains pytest fixtures and configuration
- `requirements.txt`: Project dependencies

## AWS Services Simulated

- DynamoDB: For player data and inventory storage
- S3: For file storage (not implemented in current tests)
- CloudWatch: For logging and metrics

## Notes

- Tests are designed to be isolated and reproducible
- Each test cleans up after itself
- LocalStack is used to simulate AWS services locally
- No real AWS credentials are required to run the tests 