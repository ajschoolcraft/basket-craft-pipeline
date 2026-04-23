SELECT
    product_id,
    product_name,
    created_at AS product_added_at
FROM {{ ref('stg_products') }}
