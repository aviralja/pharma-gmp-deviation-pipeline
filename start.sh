#!/bin/bash
# Production startup script for GMP Deviation API

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Start the server
cd src
python main.py
