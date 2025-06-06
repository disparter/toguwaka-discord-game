# Testing Documentation for Academia Tokugawa Discord Bot

This directory contains the test suite for the Academia Tokugawa Discord Bot. The tests are organized to mirror the structure of the main codebase, making it easy to find tests for specific components.

## Test Structure

The test directory structure follows the same pattern as the main codebase:

```
tests/
├── utils/
│   ├── game_mechanics/
│   │   ├── calculators/
│   │   │   ├── test_experience_calculator.py
│   │   │   ├── test_hp_factor_calculator.py
│   │   │   └── ...
│   │   ├── duel/
│   │   │   └── ...
│   │   └── events/
│   │       └── ...
│   └── ...
└── ...
```

Each test file is named with the prefix `test_` followed by the name of the module it tests.

## Running Tests

### Running All Tests

To run all tests in the project:

```bash
# Make sure the project root is in the Python path
PYTHONPATH=$PYTHONPATH:$(pwd) python -m unittest discover -s tests
```

### Running Tests for a Specific Module

To run tests for a specific module:

```bash
python -m unittest tests.utils.game_mechanics.calculators.test_experience_calculator
```

### Running a Specific Test Case

To run a specific test case:

```bash
python -m unittest tests.utils.game_mechanics.calculators.test_experience_calculator.TestExperienceCalculator.test_calculate_required_exp
```

## Writing Tests

When writing tests, follow these guidelines:

1. **Test Naming**: Name your test methods with the prefix `test_` followed by a descriptive name of what is being tested.
2. **Arrange-Act-Assert**: Structure your tests using the Arrange-Act-Assert pattern:
   - **Arrange**: Set up the test data and conditions
   - **Act**: Perform the action being tested
   - **Assert**: Verify the results
3. **Docstrings**: Include a docstring for each test method explaining what it tests.
4. **Edge Cases**: Include tests for edge cases and error conditions.

Example:

```python
def test_calculate_level(self):
    """Test that the calculator correctly calculates level from experience."""
    # Arrange - Set up test data
    exp_level_1 = BASE_EXP - 1
    exp_level_2 = BASE_EXP * (2 ** 1.5)

    # Act & Assert - Perform actions and verify results
    self.assertEqual(ExperienceCalculator.calculate_level(0), 1)
    self.assertEqual(ExperienceCalculator.calculate_level(exp_level_1), 1)
    self.assertEqual(ExperienceCalculator.calculate_level(exp_level_2), 2)
```

## Test Coverage

Currently, tests focus on the core game mechanics in the `utils` module. As the project grows, test coverage should be expanded to include:

- Cogs and commands
- Database interactions
- Event handling
- Story mode progression

## Continuous Integration

Tests are automatically run as part of the CI/CD pipeline in GitHub Actions before deployment. This ensures that only code that passes all tests is deployed to production.

To see the test results, check the GitHub Actions workflow runs in the repository.
