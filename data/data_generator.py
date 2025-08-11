# data/data_generator.py
"""
Generates synthetic retail sales data for the Agentic Data Explorer project.

This creates realistic-looking data with:
- Multiple product categories with different price ranges
- Regional variations in sales patterns
- Customer segments with different behaviors
- Seasonal trends and realistic date ranges
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid
from typing import List, Dict, Any

class RetailDataGenerator:
    """Generates synthetic retail sales data"""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducible data"""
        random.seed(seed)
        np.random.seed(seed)
        
        # Define business logic constants
        self.categories = {
            'Electronics': {'base_price': 299, 'margin': 0.4, 'seasonality': 1.2},
            'Clothing': {'base_price': 49, 'margin': 0.6, 'seasonality': 1.3},
            'Home & Garden': {'base_price': 89, 'margin': 0.5, 'seasonality': 0.9},
            'Sports': {'base_price': 79, 'margin': 0.45, 'seasonality': 1.1},
            'Books': {'base_price': 19, 'margin': 0.3, 'seasonality': 0.8},
            'Food & Beverage': {'base_price': 12, 'margin': 0.25, 'seasonality': 1.0}
        }
        
        self.customer_segments = {
            'Premium': {'price_multiplier': 1.5, 'quantity_preference': 2.0},
            'Standard': {'price_multiplier': 1.0, 'quantity_preference': 1.5},
            'Budget': {'price_multiplier': 0.7, 'quantity_preference': 1.0}
        }
        
        self.regions = ['North', 'South', 'East', 'West', 'Central']
        
    def generate_stores(self, num_stores: int = 100) -> List[Dict[str, Any]]:
        """Generate store master data"""
        stores = []
        
        for i in range(num_stores):
            region = random.choice(self.regions)
            store_id = f"{region}_{i+1:03d}"
            
            stores.append({
                'store_id': store_id,
                'store_name': f"{region} Store {i+1}",
                'store_location': f"{region} Region, Store #{i+1}",
                'store_region': region,
                'store_size': random.choice(['Small', 'Medium', 'Large']),
                'opening_date': datetime.now() - timedelta(days=random.randint(365, 1825))
            })
            
        return stores
    
    def generate_products(self, num_products: int = 1000) -> List[Dict[str, Any]]:
        """Generate product master data"""
        products = []
        
        for i in range(num_products):
            category = random.choice(list(self.categories.keys()))
            product_id = f"{category[:3].upper()}_{i:04d}"
            
            products.append({
                'product_id': product_id,
                'product_name': f"{category} Product {i % 100 + 1}",
                'product_category': category,
                'brand': f"Brand {chr(65 + (i % 26))}",
                'cost_price': round(self.categories[category]['base_price'] * 
                                 (1 - self.categories[category]['margin']) * 
                                 random.uniform(0.8, 1.2), 2)
            })
            
        return products
    
    def generate_sales_transactions(self, 
                                  num_transactions: int = 50000,
                                  stores: List[Dict] = None,
                                  products: List[Dict] = None,
                                  start_date: datetime = None,
                                  end_date: datetime = None) -> List[Dict[str, Any]]:
        """Generate sales transaction data"""
        
        if stores is None:
            stores = self.generate_stores()
        if products is None:
            products = self.generate_products()
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
            
        transactions = []
        
        for i in range(num_transactions):
            # Select random store and product
            store = random.choice(stores)
            product = random.choice(products)
            segment = random.choice(list(self.customer_segments.keys()))
            
            # Generate transaction date with some seasonality
            days_range = (end_date - start_date).days
            base_date = start_date + timedelta(days=random.randint(0, days_range))
            
            # Add some seasonality (higher sales in Nov-Dec, lower in Jan-Feb)
            month = base_date.month
            seasonal_factor = 1.0
            if month in [11, 12]:  # Holiday season
                seasonal_factor = 1.3
            elif month in [1, 2]:  # Post-holiday slump
                seasonal_factor = 0.7
                
            # Calculate pricing
            category_info = self.categories[product['product_category']]
            segment_info = self.customer_segments[segment]
            
            base_price = category_info['base_price']
            unit_price = (base_price * 
                         segment_info['price_multiplier'] * 
                         seasonal_factor * 
                         random.uniform(0.9, 1.1))
            
            # Quantity tends to be higher for budget customers (bulk buying)
            max_quantity = max(1, int(segment_info['quantity_preference'] * 
                                    random.uniform(1, 5)))
            quantity = random.randint(1, max_quantity)
            
            total_amount = round(unit_price * quantity, 2)
            
            transactions.append({
                'transaction_id': f"TXN_{i:08d}",
                'store_id': store['store_id'],
                'product_id': product['product_id'],
                'sale_date': base_date.date(),
                'sale_timestamp': base_date,
                'quantity': quantity,
                'unit_price': round(unit_price, 2),
                'total_amount': total_amount,
                'customer_segment': segment,
                'payment_method': random.choice(['Credit Card', 'Cash', 'Debit Card', 'Mobile Pay']),
                'discount_applied': round(random.uniform(0, 0.15) if random.random() < 0.3 else 0, 2),
                'sales_rep_id': f"REP_{random.randint(1, 50):03d}"
            })
            
        return transactions
    
    def generate_complete_dataset(self, 
                                num_stores: int = 100,
                                num_products: int = 1000, 
                                num_transactions: int = 50000) -> Dict[str, pd.DataFrame]:
        """Generate complete dataset with all tables"""
        
        print(f"Generating {num_stores} stores...")
        stores = self.generate_stores(num_stores)
        
        print(f"Generating {num_products} products...")
        products = self.generate_products(num_products)
        
        print(f"Generating {num_transactions} transactions...")
        transactions = self.generate_sales_transactions(
            num_transactions, stores, products
        )
        
        # Convert to DataFrames
        datasets = {
            'stores': pd.DataFrame(stores),
            'products': pd.DataFrame(products),
            'sales': pd.DataFrame(transactions)
        }
        
        # Add some data quality issues for testing (5% of records)
        self._add_data_quality_issues(datasets['sales'])
        
        return datasets
    
    def _add_data_quality_issues(self, sales_df: pd.DataFrame) -> None:
        """Add realistic data quality issues for testing data validation"""
        
        # Add some missing values (1% of records)
        missing_indices = sales_df.sample(frac=0.01).index
        sales_df.loc[missing_indices, 'sales_rep_id'] = None
        
        # Add some negative quantities (0.1% of records) - should be caught by tests
        negative_indices = sales_df.sample(frac=0.001).index
        sales_df.loc[negative_indices, 'quantity'] = -1
        
        # Add some zero prices (0.1% of records)
        zero_price_indices = sales_df.sample(frac=0.001).index
        sales_df.loc[zero_price_indices, 'unit_price'] = 0
    
    def save_datasets(self, datasets: Dict[str, pd.DataFrame], output_dir: str = "data/output"):
        """Save generated datasets to CSV files"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        for table_name, df in datasets.items():
            filename = f"{output_dir}/{table_name}.csv"
            df.to_csv(filename, index=False)
            print(f"Saved {len(df)} records to {filename}")
            
            # Print summary statistics
            print(f"\n{table_name.upper()} Summary:")
            print(f"  Records: {len(df):,}")
            print(f"  Columns: {len(df.columns)}")
            if table_name == 'sales':
                print(f"  Total Revenue: ${df['total_amount'].sum():,.2f}")
                print(f"  Date Range: {df['sale_date'].min()} to {df['sale_date'].max()}")
                print(f"  Avg Order Value: ${df['total_amount'].mean():.2f}")


def main():
    """Main function to generate and save sample data"""
    
    generator = RetailDataGenerator(seed=42)
    
    # Generate datasets
    datasets = generator.generate_complete_dataset(
        num_stores=100,
        num_products=1000,
        num_transactions=50000
    )
    
    # Save to files
    generator.save_datasets(datasets)
    
    print("\n✅ Data generation complete!")
    print("\nNext steps:")
    print("1. Review the generated CSV files in data/output/")
    print("2. Run the Snowflake setup script to create tables")
    print("3. Load data using data_loader.py")


if __name__ == "__main__":
    main()