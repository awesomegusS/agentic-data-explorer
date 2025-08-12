{{ config(materialized='table') }}

select
    -- Primary key
    s.transaction_id,
    
    -- Foreign keys
    s.sale_date,
    s.store_id,
    s.product_id,
    
    -- Degenerate dimensions
    s.customer_segment,
    s.payment_method,
    s.sales_rep_id,
    
    -- Measures
    s.quantity,
    s.unit_price,
    s.total_amount,
    s.discount_applied,
    
    -- Calculated measures
    s.total_amount - s.discount_applied as net_amount,
    s.quantity * s.unit_price as calculated_total,
    
    -- Date parts for easier filtering
    s.sale_year,
    s.sale_month,
    s.sale_quarter,
    s.sale_day_of_week,
    s.sale_day_name,
    
    -- Quality flags
    s.amount_calculation_correct,
    
    -- Metadata
    s.sale_timestamp as transaction_timestamp,
    current_timestamp as created_at
    
from {{ ref('stg_sales') }} s