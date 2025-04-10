#!/bin/bash

# Load .env variables into environment
export $(grep -v '^#' .env | xargs)

# Start the bot
python3 -m main.py
