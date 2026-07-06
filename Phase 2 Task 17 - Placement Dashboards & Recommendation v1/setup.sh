#!/bin/bash

# Setup script for AI Placement Recommendation System

echo "=================================="
echo "Setting up AI Recommendation System"
echo "=================================="
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Virtual environment activated"
echo

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "✓ Dependencies installed"
echo

# Create necessary directories
echo "Creating project directories..."
mkdir -p logs
mkdir -p models
mkdir -p reports

echo "✓ Directories created"
echo

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from .env.example"
else
    echo "✓ .env file already exists"
fi
echo

# Download or prepare sample data (if needed)
echo "Checking sample data..."
if [ -f data/raw/sample_students.json ] && [ -f data/raw/sample_jobs.json ]; then
    echo "✓ Sample data already exists"
else
    echo "⚠ Sample data files not found - using provided defaults"
fi
echo

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo
echo "Next steps:"
echo "1. Source virtual environment: source venv/bin/activate"
echo "2. Run demo: python demo.py"
echo "3. Start API: uvicorn src.api.app:app --reload"
echo "4. Open browser: http://localhost:8000/docs"
echo
