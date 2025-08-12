{{ config(materialized='table') }}

select
    -- Primary key
    product_id,
    
    -- Product attributes from staging
    product_name,
    product_category,
    brand,
    cost_price,
    product_group,
    price_tier,
    
    -- Metadata
    current_timestamp as created_at,
    current_timestamp as updated_at
    
from {{ ref('stg_products') }}