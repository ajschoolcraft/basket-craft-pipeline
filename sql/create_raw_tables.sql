-- Raw staging tables: mirrors of MySQL source tables
-- Truncated and reloaded each pipeline run

CREATE TABLE IF NOT EXISTS raw_orders (
    order_id            INTEGER PRIMARY KEY,
    created_at          TIMESTAMP NOT NULL,
    website_session_id  INTEGER,
    user_id             INTEGER,
    primary_product_id  INTEGER,
    items_purchased     SMALLINT NOT NULL,
    price_usd           DECIMAL(6,2) NOT NULL,
    cogs_usd            DECIMAL(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_order_items (
    order_item_id   INTEGER PRIMARY KEY,
    created_at      TIMESTAMP NOT NULL,
    order_id        INTEGER,
    product_id      INTEGER,
    is_primary_item SMALLINT NOT NULL,
    price_usd       DECIMAL(6,2) NOT NULL,
    cogs_usd        DECIMAL(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_products (
    product_id   INTEGER PRIMARY KEY,
    created_at   TIMESTAMP NOT NULL,
    product_name VARCHAR(50) NOT NULL,
    description  TEXT
);

CREATE TABLE IF NOT EXISTS raw_order_item_refunds (
    order_item_refund_id INTEGER PRIMARY KEY,
    created_at           TIMESTAMP NOT NULL,
    order_item_id        INTEGER,
    refund_amount_usd    DECIMAL(6,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_users (
    user_id                 INTEGER PRIMARY KEY,
    first_name              TEXT,
    last_name               TEXT,
    email                   TEXT,
    password_salt           TEXT,
    password_hash           TEXT,
    billing_street_address  TEXT,
    billing_city            TEXT,
    billing_state           TEXT,
    billing_postal_code     TEXT,
    billing_country         TEXT,
    shipping_street_ddress  TEXT,
    shipping_city           TEXT,
    shipping_state          TEXT,
    shipping_postal_code    TEXT,
    shipping_country        TEXT,
    created_at              TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_employees (
    employee_id INTEGER PRIMARY KEY,
    first_name  VARCHAR(50),
    last_name   VARCHAR(50),
    department  VARCHAR(50),
    salary      DECIMAL(10,2),
    email       VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS raw_website_sessions (
    website_session_id INTEGER PRIMARY KEY,
    created_at         TIMESTAMP NOT NULL,
    user_id            INTEGER,
    is_repeat_session  SMALLINT NOT NULL,
    utm_source         VARCHAR(12),
    utm_campaign       VARCHAR(20),
    utm_content        VARCHAR(15),
    device_type        VARCHAR(15),
    http_referer       VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS raw_website_pageviews (
    website_pageview_id INTEGER PRIMARY KEY,
    created_at          TIMESTAMP NOT NULL,
    website_session_id  INTEGER,
    pageview_url        VARCHAR(50) NOT NULL
);
