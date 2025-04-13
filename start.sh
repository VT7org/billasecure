#!/bin/bash

# Exit on error
set -e

# Load .env variables (skip comments & blank lines)
if [ -f .env ]; then
  export $(grep -vE '^\s*#' .env | grep -vE '^\s*$' | xargs)
fi

# Start Flask server in background
python3 vxcore.py &
FLASK_PID=$!

# Handle Ctrl+C and SIGTERM to shut down Flask too
trap "echo 'Stopping...'; kill $FLASK_PID; exit" SIGINT SIGTERM

# Start the bot (blocking)
python3 main.py

# Clean up Flask process if bot exits
kill $FLASK_PID
