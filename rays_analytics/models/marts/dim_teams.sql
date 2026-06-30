with teams as (

    select
        home_team_id    as team_id,
        home_team_name  as team_name,
        game_date
    from {{ ref('stg_games') }}

    union all

    select
        away_team_id    as team_id,
        away_team_name  as team_name,
        game_date
    from {{ ref('stg_games') }}

),

-- a team_id can map to more than one name over time (e.g. relocations,
-- rebrands). Keep only the name tied to that team's most recent game.
ranked as (

    select
        team_id,
        team_name,
        row_number() over (
            partition by team_id
            order by game_date desc
        ) as rn
    from teams

)

select
    team_id,
    team_name
from ranked
where rn = 1
order by team_name