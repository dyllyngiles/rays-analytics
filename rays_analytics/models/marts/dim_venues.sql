with venues as (

    select distinct
        venue_id,
        venue_name
    from {{ ref('stg_games') }}
    where venue_id is not null

)

select
    venue_id,
    venue_name
from venues
order by venue_name