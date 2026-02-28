#!/bin/bash

# SmartPesa - Clean Cache Script

echo "🧹 Cleaning Python cache files..."

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

echo "✅ Done"
