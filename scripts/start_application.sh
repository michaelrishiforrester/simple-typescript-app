#!/bin/bash
echo "Starting application: $(date)"
cd /var/www/html/typescript-app

# Install PM2 if not already installed
if ! command -v pm2 &> /dev/null; then
    echo "PM2 not found, installing globally"
    npm install -g pm2
fi

# Start the application
pm2 start dist/app.js --name "typescript-app" --env production
pm2 save

# Set up PM2 to start on system boot
pm2 startup | tail -n 1 | bash

echo "Application startup completed: $(date)"