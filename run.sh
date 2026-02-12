#!/bin/bash
# Run script for GitHub Scraper API

set -e

echo "=================================="
echo "GitHub Scraper FastAPI"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your settings!"
fi

# Create data directory
mkdir -p data/exports

echo ""
echo "=================================="
echo "Starting API Server"
echo "=================================="
echo ""
echo "📍 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
