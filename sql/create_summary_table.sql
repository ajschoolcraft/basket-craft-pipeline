CREATE TABLE IF NOT EXISTS monthly_sales_summary (
    id              SERIAL PRIMARY KEY,
    year_month      DATE NOT NULL,
    product_name    VARCHAR(100) NOT NULL,
    total_revenue   DECIMAL(12,2) NOT NULL,
    total_refunds   DECIMAL(12,2) NOT NULL,
    net_revenue     DECIMAL(12,2) NOT NULL,
    order_count     INTEGER NOT NULL,
    avg_order_value DECIMAL(10,2) NOT NULL,
    total_cogs      DECIMAL(12,2) NOT NULL,
    gross_profit    DECIMAL(12,2) NOT NULL,
    margin_pct      DECIMAL(5,2) NOT NULL,
    updated_at      TIMESTAMP NOT NULL,
    UNIQUE (year_month, product_name)
);
