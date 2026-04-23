select
    date_trunc('month', oi.created_at)::date    as year_month,
    p.product_name,
    sum(oi.price_usd)                           as total_revenue,
    coalesce(sum(r.refund_amount_usd), 0)       as total_refunds,
    sum(oi.price_usd)
        - coalesce(sum(r.refund_amount_usd), 0) as net_revenue,
    count(distinct oi.order_id)                 as order_count,
    (sum(oi.price_usd) - coalesce(sum(r.refund_amount_usd), 0))
        / nullif(count(distinct oi.order_id), 0)
                                                as avg_order_value,
    sum(oi.cogs_usd)                            as total_cogs,
    (sum(oi.price_usd) - coalesce(sum(r.refund_amount_usd), 0))
        - sum(oi.cogs_usd)                      as gross_profit,
    ((sum(oi.price_usd) - coalesce(sum(r.refund_amount_usd), 0))
        - sum(oi.cogs_usd))
        / nullif(sum(oi.price_usd)
        - coalesce(sum(r.refund_amount_usd), 0), 0)
        * 100                                   as margin_pct,
    current_timestamp()                         as updated_at
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_products') }} p
    on p.product_id = oi.product_id
left join (
    select
        order_item_id,
        sum(refund_amount_usd) as refund_amount_usd
    from {{ ref('stg_order_item_refunds') }}
    group by order_item_id
) r
    on r.order_item_id = oi.order_item_id
group by 1, 2
