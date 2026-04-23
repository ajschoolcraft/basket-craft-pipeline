SELECT
    DATE_TRUNC('month', oi.created_at)::DATE                    AS year_month,
    oi.product_id,
    ws.device_type,
    u.billing_state,
    u.billing_country,
    COUNT(DISTINCT oi.order_id)                                 AS order_count,
    SUM(oi.price_usd)                                           AS total_revenue,
    COALESCE(SUM(r.refund_amount_usd), 0)                       AS total_refunds,
    SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)   AS net_revenue,
    SUM(oi.cogs_usd)                                            AS total_cogs,
    SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)
        - SUM(oi.cogs_usd)                                      AS gross_profit,
    (SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)
        - SUM(oi.cogs_usd))
        / NULLIF(SUM(oi.price_usd)
        - COALESCE(SUM(r.refund_amount_usd), 0), 0) * 100       AS margin_pct,
    (SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0))
        / NULLIF(COUNT(DISTINCT oi.order_id), 0)                AS avg_order_value
FROM {{ ref('stg_order_items') }} oi
INNER JOIN {{ ref('stg_orders') }} o
    ON o.order_id = oi.order_id
INNER JOIN {{ ref('stg_users') }} u
    ON u.user_id = o.user_id
LEFT JOIN {{ ref('stg_website_sessions') }} ws
    ON ws.website_session_id = o.website_session_id
LEFT JOIN (
    SELECT
        order_item_id,
        SUM(refund_amount_usd) AS refund_amount_usd
    FROM {{ ref('stg_order_item_refunds') }}
    GROUP BY order_item_id
) r
    ON r.order_item_id = oi.order_item_id
GROUP BY 1, 2, 3, 4, 5
