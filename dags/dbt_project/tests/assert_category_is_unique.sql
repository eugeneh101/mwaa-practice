select
    catgroup, count(1) as row_count
from {{ source("tickit", "category") }}
group by 1
having row_count > 1 -- should fail