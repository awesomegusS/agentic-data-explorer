#!/bin/bash
# Load environment variables from .env file

if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
    echo "Account: $SNOWFLAKE_ACCOUNT"
    echo "User: $SNOWFLAKE_USER"
    echo "Database: $SNOWFLAKE_DATABASE"
else
    echo "❌ .env file not found"
fi