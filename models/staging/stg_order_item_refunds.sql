select
    order_item_refund_id,
    created_at as refunded_at,
    order_item_id,
    refund_amount_usd
from {{ source('raw', 'raw_order_item_refunds') }}
