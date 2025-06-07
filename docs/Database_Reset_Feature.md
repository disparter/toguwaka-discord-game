# Database Reset Feature

## Overview
This document describes the new database reset feature added to the Tokugawa Discord Game. This feature allows for a complete reset of the database, clearing both the SQLite `.db` file and DynamoDB data, enabling a fresh start with an empty database.

## Configuration
The database reset feature is controlled by the `RESET_DATABASE` environment variable in the `.env` file:

```
# Database Reset Configuration
# Set to true to reset the database completely (clear .db file and DynamoDB)
# WARNING: This will delete all data! Use with caution.
# Default: false
RESET_DATABASE=false
```

## How It Works
When the `RESET_DATABASE` flag is set to `true`, the following actions occur during application startup:

1. For SQLite database:
   - The SQLite database file (`data/tokugawa.db`) is deleted
   - A new empty database file is created with the default schema

2. For DynamoDB:
   - All items in the DynamoDB table are deleted
   - The table structure remains intact, but all data is removed

## Usage Instructions

### To Reset the Database
1. Edit the `.env` file and set `RESET_DATABASE=true`
2. Start the application
3. The database will be reset during initialization
4. After the first run, set `RESET_DATABASE=false` to prevent accidental resets in subsequent runs

### Important Notes
- **WARNING**: This is a destructive operation that will delete ALL data in the database
- Always backup your data before performing a reset if you need to preserve any information
- The reset occurs at application startup, before any other database operations
- After resetting, the application will create a new empty database with the default schema

## Implementation Details
The reset functionality is implemented in two files:

1. `utils/database.py` - Handles SQLite database reset
2. `utils/dynamodb.py` - Handles DynamoDB reset

Both implementations check the `RESET_DATABASE` environment variable during initialization and perform the reset if it's set to `true`.

## Troubleshooting
If you encounter issues with the database reset feature:

1. Check the application logs for error messages
2. Verify that you have appropriate permissions to delete and create files in the data directory
3. For DynamoDB, ensure that your AWS credentials have sufficient permissions to delete items from the table