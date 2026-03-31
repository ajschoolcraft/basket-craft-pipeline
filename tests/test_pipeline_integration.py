"""
Integration tests — run manually against Docker.

Prerequisites:
    docker compose up -d postgres
    docker compose run --rm pipeline

Checks:
    1. Pipeline exits 0
    2. Raw tables have expected row counts
    3. monthly_sales_summary has rows grouped by month + product
    4. Running pipeline twice produces same row count (idempotent)
"""
