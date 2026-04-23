select
    employee_id,
    first_name,
    last_name,
    department,
    salary,
    email
from {{ source('raw', 'raw_employees') }}
