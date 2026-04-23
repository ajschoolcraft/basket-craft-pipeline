select
    product_id,
    created_at,
    trim(product_name) as product_name,
    description
from {{ source('raw', 'raw_products') }}
