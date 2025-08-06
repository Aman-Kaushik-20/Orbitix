#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
export PYTHONDONTWRITEBYTECODE=1
find . -type d -name "__pycache__" -exec rm -rf {} +; find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
echo "→ Changing to the 'backend' directory..."
cd backend

echo "-> Activating .venv "
source .venv/bin/activate
# if .venv not there, do -> uv venv --seed
echo "→ Installing dependencies..."
uv pip install -e .[dev]

echo "🚀 Starting the backend server..."
echo  "Sohail Ji 🥰🥰 yaha par jao 👉 http://localhost:8080/docs "
python main.py