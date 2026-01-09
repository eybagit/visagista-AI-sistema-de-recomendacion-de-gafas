#!/usr/bin/env bash
# exit on error
set -o errexit

# Build frontend
npm install
npm run build

# Install pipenv if not available
pip install pipenv

# Install Python dependencies from Pipfile
pipenv install --deploy

# Run database migrations using pipenv script
pipenv run upgrade
