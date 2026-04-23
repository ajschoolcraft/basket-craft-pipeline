select
    order_id,
    created_at,
    website_session_id,
    user_id,
    primary_product_id,
    items_purchased,
    price_usd,
    cogs_usd,
    price_usd - cogs_usd as profit_usd
from {{ source('raw', 'raw_orders') }}
