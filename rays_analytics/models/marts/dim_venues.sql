with venues as (

    select
        venue_id,
        venue_name,
        game_date
    from {{ ref('stg_games') }}
    where venue_id is not null

),

-- a venue_id can map to more than one name over time (sponsorship
-- naming-rights changes). Keep only the name tied to its most recent game.
ranked as (

    select
        venue_id,
        venue_name,
        row_number() over (
            partition by venue_id
            order by game_date desc
        ) as rn
    from venues

)

select
    venue_id,
    venue_name
from ranked
where rn = 1
order by venue_name