{{ config(materialized='table') }}

with date_spine as (
    select distinct sale_date as date_day
    from {{ ref('stg_sales') }}
),

date_details as (
    select
        -- Primary key
        date_day,
        
        -- Date parts
        extract(year from date_day) as year,
        extract(quarter from date_day) as quarter,
        extract(month from date_day) as month,
        extract(week from date_day) as week_of_year,
        extract(day from date_day) as day_of_month,
        extract(dayofweek from date_day) as day_of_week,
        extract(dayofyear from date_day) as day_of_year,
        
        -- Day names
        dayname(date_day) as day_name,
        monthname(date_day) as month_name,
        
        -- Business calendar
        case 
            when extract(dayofweek from date_day) in (1, 7) then 'Weekend'
            else 'Weekday'
        end as day_type,
        
        case
            when extract(month from date_day) in (12, 1, 2) then 'Winter'
            when extract(month from date_day) in (3, 4, 5) then 'Spring'
            when extract(month from date_day) in (6, 7, 8) then 'Summer'
            when extract(month from date_day) in (9, 10, 11) then 'Fall'
        end as season,
        
        -- Fiscal periods (assuming Jan-Dec fiscal year)
        extract(year from date_day) as fiscal_year,
        'Q' || extract(quarter from date_day) as fiscal_quarter
        
    from date_spine
)

select * from date_details