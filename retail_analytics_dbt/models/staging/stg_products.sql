{{ config(materialized='view') }}

select
    -- Primary key
    product_id,
    
    -- Product attributes
    product_name,
    product_category,
    brand,
    cost_price,
    
    -- Product groupings for analysis
    case
        when product_category = 'Electronics' then 'High-Tech'
        when product_category in ('Clothing', 'Sports') then 'Lifestyle'
        when product_category in ('Home & Garden', 'Food & Beverage') then 'Essentials'
        when product_category = 'Books' then 'Media'
        else 'Other'
    end as product_group,
    
    -- Price tiers
    case
        when cost_price >= 200 then 'Premium'
        when cost_price >= 50 then 'Standard'
        else 'Budget'
    end as price_tier,
    
    -- Metadata
    _loaded_at,
    _source_file
    
from {{ source('raw_retail', 'products') }}
where product_id is not null