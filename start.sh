#!/bin/bash

# Load .env variables safely
set -o allexport
source <(grep -v '^#' .env | grep '=')
set +o allexport

# Exit if any command fails
set -e

# Start the bot
python3 -m main.py
