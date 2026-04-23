select
    website_pageview_id,
    created_at,
    website_session_id,
    pageview_url
from {{ source('raw', 'raw_website_pageviews') }}
