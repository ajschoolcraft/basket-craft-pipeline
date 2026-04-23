SELECT DISTINCT
    DATE_TRUNC('month', created_at)::DATE AS year_month,
    EXTRACT(YEAR FROM created_at)         AS year,
    EXTRACT(QUARTER FROM created_at)      AS quarter,
    EXTRACT(MONTH FROM created_at)        AS month_number,
    TO_CHAR(created_at, 'Mon')            AS month_name
FROM {{ ref('stg_orders') }}
