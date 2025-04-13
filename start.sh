#!/bin/bash

# Exit if any command fails
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Start the Flask API server (vxcore) in the background
python3 vxcore.py &

# Start the Telegram bot
python3 main.py
