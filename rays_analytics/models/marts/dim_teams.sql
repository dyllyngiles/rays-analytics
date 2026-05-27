with teams as (

    select distinct
        home_team_id    as team_id,
        home_team_name  as team_name
    from {{ ref('stg_games') }}

    union

    select distinct
        away_team_id    as team_id,
        away_team_name  as team_name
    from {{ ref('stg_games') }}

)

select
    team_id,
    team_name
from teams
order by team_name