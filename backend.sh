#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
export PYTHONDONTWRITEBYTECODE=1
find . -type d -name "__pycache__" -exec rm -rf {} +; find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

echo "→ Changing to the 'backend' directory..."
cd backend

echo "→ Creating a virtual environment if it doesn't exist..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "→ Activating .venv"
source .venv/bin/activate

echo "→ Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "🚀 Starting the backend server..."
echo "Sohail Ji 🥰🥰 yaha par jao 👉 http://localhost:8080/docs"
python main.py