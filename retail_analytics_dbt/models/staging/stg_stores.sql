{{ config(materialized='view') }}

select
    -- Primary key
    store_id,
    
    -- Store attributes
    store_name,
    store_location,
    store_region,
    store_size,
    opening_date,
    
    -- Calculated fields
    current_date - opening_date as days_open,
    case
        when current_date - opening_date > 1095 then 'Established' -- 3+ years
        when current_date - opening_date > 365 then 'Mature'      -- 1+ years
        else 'New'                                                 -- < 1 year
    end as store_age_category,
    
    -- Regional groupings for analysis
    case
        when store_region in ('North', 'East') then 'Northeast'
        when store_region in ('South', 'Central') then 'South-Central'
        else 'West'
    end as region_group,
    
    -- Metadata
    _loaded_at,
    _source_file
    
from {{ source('raw_retail', 'stores') }}
where store_id is not null