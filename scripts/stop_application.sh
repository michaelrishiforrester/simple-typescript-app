#!/bin/bash
echo "Stopping application: $(date)"
cd /var/www/html/typescript-app

# Install PM2 if not already installed
if ! command -v pm2 &> /dev/null; then
    echo "PM2 not found, installing globally"
    npm install -g pm2
fi

# Stop any existing instance
pm2 stop typescript-app || echo "Application was not running"
echo "Application stop completed: $(date)"