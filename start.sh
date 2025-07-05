#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting Skill_connect application on Render..."

# Run database migrations (if applicable)
# Render's build process usually installs everything first.
# This assumes 'flask' command is available after dependencies are installed.
echo "Running database migrations..."
# Check if Flask-Migrate is installed and commands exist
if command -v flask &> /dev/null && flask db --help &> /dev/null; then
    flask db upgrade
else
    echo "Flask-Migrate commands not found or not configured. Skipping migrations."
    echo "If you have migrations, ensure 'flask db' command is available and configured."
fi

# Start the Gunicorn server
# Render sets the PORT environment variable automatically
# and expects your app to listen on it.
echo "Starting Gunicorn server..."
gunicorn app:app --workers 4 --bind 0.0.0.0:"$PORT"

echo "Application started."