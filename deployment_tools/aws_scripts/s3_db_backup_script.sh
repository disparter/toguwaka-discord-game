#!/bin/bash

# Script to backup the SQLite database to an S3 bucket
# This script uses the AWS CLI, which must be installed and configured with appropriate credentials

# Configuration
S3_BUCKET="tokugawa-db-storage"
LOCAL_DB="data/tokugawa.db"

# Check if the database file exists
if [ -f "$LOCAL_DB" ]; then
    # Upload the database file to S3
    aws s3 cp "$LOCAL_DB" "s3://$S3_BUCKET/tokugawa.db" && echo "Upload to S3 completed successfully!" || echo "Error uploading to S3."
else
    echo "Database file not found: $LOCAL_DB"
fi