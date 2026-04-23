SELECT DISTINCT
    device_type
FROM {{ ref('stg_website_sessions') }}
WHERE device_type IS NOT NULL
