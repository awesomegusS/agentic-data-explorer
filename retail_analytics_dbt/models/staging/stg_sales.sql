{{ config(materialized='view') }}

with source_data as (
    select * from {{ source('raw_retail', 'sales') }}
),

cleaned_data as (
    select
        -- Primary keys
        transaction_id,
        store_id,
        product_id,
        
        -- Dates
        sale_date,
        sale_timestamp,
        
        -- Metrics
        quantity,
        unit_price,
        total_amount,
        discount_applied,
        
        -- Dimensions
        customer_segment,
        payment_method,
        sales_rep_id,
        
        -- Calculated fields for easier querying
        extract(year from sale_date) as sale_year,
        extract(month from sale_date) as sale_month,
        extract(quarter from sale_date) as sale_quarter,
        extract(dayofweek from sale_date) as sale_day_of_week,
        dayname(sale_date) as sale_day_name,
        
        -- Data quality indicator
        case 
            when abs(total_amount - (quantity * unit_price)) < 0.01 then true 
            else false 
        end as amount_calculation_correct,
        
        -- Metadata
        _loaded_at,
        _source_file
        
    from source_data
    
    -- Basic data quality filters
    where transaction_id is not null
      and quantity > 0
      and unit_price > 0
      and total_amount > 0
      and sale_date is not null
)

select * from cleaned_data