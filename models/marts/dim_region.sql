SELECT DISTINCT
    billing_state,
    billing_country
FROM {{ ref('stg_users') }}
WHERE billing_country IS NOT NULL
