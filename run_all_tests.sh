#!/bin/bash
# Run all Python test files individually, ensuring sys.path modifications are respected
export PYTHONPATH="$PYTHONPATH:$(pwd)"

find tests -name "test_*.py" | while read test_file; do
    echo "Running $test_file"
    python "$test_file"
done 