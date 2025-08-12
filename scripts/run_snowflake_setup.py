#!/usr/bin/env python3
"""
Run Snowflake setup SQL from Python
"""

import snowflake.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_sql_file(sql_file_path):
    """Run SQL file against Snowflake"""
    
    # Read SQL file
    with open(sql_file_path, 'r') as file:
        sql_content = file.read()
    
    # Split into individual statements (simple split on semicolon)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            role=os.getenv('SNOWFLAKE_ROLE')
        )
        
        cursor = conn.cursor()
        
        print(f"🚀 Running {len(statements)} SQL statements...")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"  [{i}/{len(statements)}] Executing...")
                cursor.execute(statement)
                print(f"  ✅ Statement {i} completed")
        
        # Verify setup
        print("\n🔍 Verifying setup...")
        cursor.execute("SHOW DATABASES LIKE 'RETAIL_ANALYTICS'")
        result = cursor.fetchall()
        
        if result:
            print("✅ Database 'retail_analytics' created successfully!")
            
            # Check tables
            cursor.execute("USE DATABASE retail_analytics")
            cursor.execute("USE SCHEMA raw")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"✅ Created {len(tables)} tables: {[table[1] for table in tables]}")
        else:
            print("❌ Database verification failed")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Snowflake setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_sql_file("data/snowflake_setup.sql")
    if not success:
        exit(1)