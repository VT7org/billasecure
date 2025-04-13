#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Load .env variables safely (ignore comments and blank lines)
if [ -f .env ]; then
  export $(grep -vE '^\s*#' .env | grep -vE '^\s*$' | xargs)
fi

# Start the bot
python3 -m main.py
