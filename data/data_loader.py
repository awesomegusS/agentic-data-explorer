# data/data_loader.py
"""
Snowflake data loader for the Agentic Data Explorer project.
"""

import os
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from dotenv import load_dotenv
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_loader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SnowflakeDataLoader:
    """Handles data loading operations to Snowflake"""
    
    def __init__(self):
        """Initialize Snowflake connection using environment variables"""
        
        # Validate required environment variables
        required_vars = [
            'SNOWFLAKE_USER', 'SNOWFLAKE_PASSWORD', 'SNOWFLAKE_ACCOUNT',
            'SNOWFLAKE_DATABASE', 'SNOWFLAKE_WAREHOUSE'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        self.connection_params = {
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'database': os.getenv('SNOWFLAKE_DATABASE', 'retail_analytics'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA', 'raw')
        }
        
        self.connection = None
        
    def connect(self) -> None:
        """Establish connection to Snowflake"""
        try:
            logger.info("Connecting to Snowflake...")
            self.connection = snowflake.connector.connect(**self.connection_params)
            logger.info("✅ Successfully connected to Snowflake")
            
            # Test connection with a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            logger.info(f"Snowflake version: {version}")
            cursor.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Snowflake: {str(e)}")
            raise
            
    def disconnect(self) -> None:
        """Close Snowflake connection"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from Snowflake")
    
    def load_csv_to_table(self, 
                          csv_file_path: str, 
                          table_name: str,
                          schema: str = 'raw',
                          truncate_first: bool = False) -> Dict[str, any]:
        """Load CSV file to Snowflake table using pandas"""
        
        if not self.connection:
            raise ConnectionError("Not connected to Snowflake")
            
        file_path = Path(csv_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
            
        logger.info(f"Loading {csv_file_path} to {schema}.{table_name}")
        
        start_time = datetime.now()
        
        try:
            # Read CSV file
            logger.info("Reading CSV file...")
            df = pd.read_csv(csv_file_path)
            original_row_count = len(df)
            logger.info(f"Found {original_row_count:,} rows in CSV")
            
            # Clean column names - remove any special characters
            df.columns = df.columns.str.strip().str.upper()
            logger.info(f"Columns: {list(df.columns)}")
            
            # Clean and validate data
            df_clean = self._clean_data(df, table_name)
            
            if truncate_first:
                logger.info(f"Truncating table {schema}.{table_name}")
                cursor = self.connection.cursor()
                cursor.execute(f"TRUNCATE TABLE {schema}.{table_name}")
                cursor.close()
            
            # Add metadata columns (uppercase to match Snowflake)
            df_clean['_LOADED_AT'] = datetime.now()
            df_clean['_SOURCE_FILE'] = file_path.name
            
            # Load data using pandas with explicit settings
            logger.info("Loading data to Snowflake...")
            
            success, nchunks, nrows, _ = write_pandas(
                conn=self.connection,
                df=df_clean,
                table_name=table_name.upper(),
                schema=schema.upper(),
                auto_create_table=False,
                overwrite=False,
                quote_identifiers=False  # This is key - don't quote identifiers
            )
            
            if success:
                logger.info(f"✅ Successfully loaded {nrows:,} rows")
                return {
                    'table_name': f"{schema}.{table_name}",
                    'source_file': csv_file_path,
                    'original_rows': original_row_count,
                    'loaded_rows': nrows,
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'success': True
                }
            else:
                logger.error("❌ Failed to load data")
                return {
                    'table_name': f"{schema}.{table_name}",
                    'source_file': csv_file_path,
                    'original_rows': original_row_count,
                    'loaded_rows': 0,
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'success': False,
                    'error': 'Write operation failed'
                }
                    
        except Exception as e:
            logger.error(f"❌ Error loading data: {str(e)}")
            return {
                'table_name': f"{schema}.{table_name}",
                'source_file': csv_file_path,
                'original_rows': original_row_count if 'original_row_count' in locals() else 0,
                'loaded_rows': 0,
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'success': False,
                'error': str(e)
            }
    
    def _clean_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Clean and validate data"""
        
        df_clean = df.copy()
        
        if table_name.lower() == 'sales':
            # Convert date columns (handle uppercase column names)
            date_col = 'SALE_DATE' if 'SALE_DATE' in df_clean.columns else 'sale_date'
            if date_col in df_clean.columns:
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce').dt.date
            
            timestamp_col = 'SALE_TIMESTAMP' if 'SALE_TIMESTAMP' in df_clean.columns else 'sale_timestamp'
            if timestamp_col in df_clean.columns:
                df_clean[timestamp_col] = pd.to_datetime(df_clean[timestamp_col], errors='coerce')
        
        elif table_name.lower() == 'stores':
            # Convert opening_date
            date_col = 'OPENING_DATE' if 'OPENING_DATE' in df_clean.columns else 'opening_date'
            if date_col in df_clean.columns:
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce').dt.date
        
        # Remove any completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Replace NaN with None for better Snowflake compatibility
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        
        return df_clean
    
    def load_all_tables(self, data_directory: str = "data/output") -> Dict[str, any]:
        """Load all CSV files to corresponding tables"""
        
        data_path = Path(data_directory)
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {data_directory}")
        
        # Define table mapping
        table_mapping = {
            'stores.csv': 'stores',
            'products.csv': 'products', 
            'sales.csv': 'sales'
        }
        
        results = {}
        
        # Load tables in dependency order (master data first)
        load_order = ['stores.csv', 'products.csv', 'sales.csv']
        
        for csv_file in load_order:
            csv_path = data_path / csv_file
            if csv_path.exists():
                table_name = table_mapping[csv_file]
                logger.info(f"\n{'='*20} Loading {table_name} {'='*20}")
                
                try:
                    result = self.load_csv_to_table(
                        str(csv_path), 
                        table_name,
                        truncate_first=True  # Fresh load
                    )
                    results[table_name] = result
                    
                    # Log results
                    logger.info(f"✅ {table_name}: {result['loaded_rows']:,} rows loaded in {result['duration_seconds']:.1f}s")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to load {table_name}: {str(e)}")
                    results[table_name] = {'error': str(e)}
            else:
                logger.warning(f"⚠️  CSV file not found: {csv_path}")
        
        return results

def main():
    """Main function to load all data"""
    
    print("🚀 Starting Snowflake Data Loading Process")
    print("="*50)
    
    loader = None
    
    try:
        # Initialize loader and connect
        loader = SnowflakeDataLoader()
        loader.connect()
        
        # Load all tables
        results = loader.load_all_tables()
        
        # Print final summary
        print("\n" + "="*50)
        print("🎉 DATA LOADING COMPLETE!")
        print("="*50)
        
        total_rows = sum(r.get('loaded_rows', 0) for r in results.values() if isinstance(r, dict))
        print(f"Total rows loaded: {total_rows:,}")
        
        errors = [table for table, result in results.items() if 'error' in result]
        if errors:
            print(f"❌ Tables with errors: {errors}")
        else:
            print("✅ All tables loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Critical error: {str(e)}")
        sys.exit(1)
        
    finally:
        if loader:
            loader.disconnect()

if __name__ == "__main__":
    main()