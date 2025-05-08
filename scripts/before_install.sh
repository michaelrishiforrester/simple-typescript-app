#!/bin/bash
echo "Before installation script starting: $(date)"
# Create application directory if it doesn't exist
mkdir -p /var/www/html/typescript-app
# Check for previous installation and backup if exists
if [ -d "/var/www/html/typescript-app/dist" ]; then
  echo "Found existing installation, creating backup"
  timestamp=$(date +%Y%m%d%H%M%S)
  mkdir -p /var/www/html/backups
  cp -R /var/www/html/typescript-app /var/www/html/backups/typescript-app-$timestamp
fi
echo "Before installation script completed: $(date)"