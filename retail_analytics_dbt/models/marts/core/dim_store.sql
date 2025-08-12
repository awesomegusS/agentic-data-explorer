{{ config(materialized='table') }}

select
    -- Primary key
    store_id,
    
    -- Store attributes from staging
    store_name,
    store_location,
    store_region,
    store_size,
    opening_date,
    store_age_category,
    region_group,
    days_open,
    
    -- Additional calculated fields
    case
        when store_size = 'Large' then 3
        when store_size = 'Medium' then 2
        else 1
    end as size_rank,
    
    -- Metadata
    current_timestamp as created_at,
    current_timestamp as updated_at
    
from {{ ref('stg_stores') }}