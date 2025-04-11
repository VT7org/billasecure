#!/bin/bash

# Backup the original .env
cp .env .env.bak

# Clean .env: keep only valid KEY=value lines
grep -E '^[A-Za-z_][A-Za-z0-9_]*=.*' .env > .env.cleaned

# Overwrite .env with cleaned version
mv .env.cleaned .env

echo "✅ .env file cleaned. Backup saved as .env.bak"
