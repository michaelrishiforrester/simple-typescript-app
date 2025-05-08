#!/bin/bash
echo "After installation script starting: $(date)"
cd /var/www/html/typescript-app

# Install production dependencies only
npm install --production

# Set proper permissions
chmod -R 755 /var/www/html/typescript-app
echo "After installation script completed: $(date)"