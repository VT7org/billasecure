#!/bin/bash

# Exit on error
set -e

# Load env vars
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Start Flask server in background
python3 vxcore.py &
FLASK_PID=$!

# Trap Ctrl+C (SIGINT) to stop both
trap "echo 'Stopping...'; kill $FLASK_PID; exit" SIGINT SIGTERM

# Start the bot (this will block)
python3 main.py

# Cleanup after bot exits
kill $FLASK_PID
