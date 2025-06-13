#!/bin/bash

# Test runner script for the Organisize project
# Run this script to execute all tests with coverage reporting

echo "Starting test automation for Organisize..."

# Set up environment
if [ ! -d "venv_fresh" ]; then
    echo "Creating virtual environment..."
    python -m venv venv_fresh
fi

# Activate virtual environment
source venv_fresh/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Run tests with coverage
echo "Running tests with coverage..."
coverage run --source='.' manage.py test planner

# Generate coverage report
echo "Generating coverage report..."
coverage report

# Generate HTML coverage report
echo "Generating HTML coverage report..."
coverage html

echo "Test automation complete!"
echo "Coverage report available in htmlcov/index.html"

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed! Ready for deployment."
    exit 0
else
    echo "❌ Tests failed! Deployment blocked."
    exit 1
fi