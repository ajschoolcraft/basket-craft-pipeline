select
    order_item_id,
    created_at,
    order_id,
    product_id,
    is_primary_item = 1 as is_primary_item,
    price_usd,
    cogs_usd,
    price_usd - cogs_usd as profit_usd
from {{ source('raw', 'raw_order_items') }}
