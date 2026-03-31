INSERT INTO monthly_sales_summary
    (year_month, product_name, total_revenue, total_refunds, net_revenue,
     order_count, avg_order_value, total_cogs, gross_profit, margin_pct, updated_at)
SELECT
    DATE_TRUNC('month', oi.created_at)::DATE       AS year_month,
    p.product_name,
    SUM(oi.price_usd)                              AS total_revenue,
    COALESCE(SUM(r.refund_amount_usd), 0)          AS total_refunds,
    SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)
                                                    AS net_revenue,
    COUNT(DISTINCT oi.order_id)                     AS order_count,
    (SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0))
        / NULLIF(COUNT(DISTINCT oi.order_id), 0)   AS avg_order_value,
    SUM(oi.cogs_usd)                               AS total_cogs,
    (SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)) - SUM(oi.cogs_usd)
                                                    AS gross_profit,
    ((SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0)) - SUM(oi.cogs_usd))
        / NULLIF(SUM(oi.price_usd) - COALESCE(SUM(r.refund_amount_usd), 0), 0) * 100
                                                    AS margin_pct,
    NOW()                                           AS updated_at
FROM raw_order_items oi
JOIN raw_products p ON p.product_id = oi.product_id
LEFT JOIN (
    SELECT order_item_id, SUM(refund_amount_usd) AS refund_amount_usd
    FROM raw_order_item_refunds
    GROUP BY order_item_id
) r ON r.order_item_id = oi.order_item_id
GROUP BY 1, 2
ON CONFLICT (year_month, product_name)
DO UPDATE SET
    total_revenue   = EXCLUDED.total_revenue,
    total_refunds   = EXCLUDED.total_refunds,
    net_revenue     = EXCLUDED.net_revenue,
    order_count     = EXCLUDED.order_count,
    avg_order_value = EXCLUDED.avg_order_value,
    total_cogs      = EXCLUDED.total_cogs,
    gross_profit    = EXCLUDED.gross_profit,
    margin_pct      = EXCLUDED.margin_pct,
    updated_at      = EXCLUDED.updated_at;
