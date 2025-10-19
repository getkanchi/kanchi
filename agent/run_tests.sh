#!/bin/bash
# Test runner script for Kanchi backend tests

set -e

echo "========================================="
echo "Running Kanchi Backend Tests"
echo "========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Run all unit tests with verbose output
echo "Running unit tests..."
poetry run python -m unittest discover -s tests/unit -v

echo ""
echo "========================================="
echo "✓ All tests passed!"
echo "========================================="
echo ""

# Optional: Run with coverage (requires pytest and pytest-cov)
# Uncomment to enable coverage reporting:
# echo "Running tests with coverage..."
# poetry add --group dev pytest-cov
# poetry run pytest tests/ --cov=services --cov=database --cov-report=term-missing
