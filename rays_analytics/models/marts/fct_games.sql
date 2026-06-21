with games as (

    select * from {{ ref('stg_games') }}

),

venues as (

    select * from {{ ref('dim_venues') }}

),

rays_perspective as (

    select
        game_id,
        game_date,
        game_started_at,
        season,
        venue_id,
        venue_name,
        game_status,
        home_team_id = 139                                                      as is_home_game,
        case when home_team_id = 139 then 'home' else 'away' end                as game_location,
        case when home_team_id = 139 then away_team_id else home_team_id end    as opponent_team_id,
        case when home_team_id = 139 then away_team_name else home_team_name end as opponent_team_name,
        case when home_team_id = 139 then home_score else away_score end        as rays_runs_scored,
        case when home_team_id = 139 then away_score else home_score end        as rays_runs_allowed
    from games

),

final as (

    select
        game_id,
        game_date,
        game_started_at,
        season,
        game_location,
        is_home_game,
        opponent_team_id,
        opponent_team_name,
        venue_id,
        venue_name,
        rays_runs_scored,
        rays_runs_allowed,
        case when rays_runs_scored > rays_runs_allowed then 1 else 0 end        as rays_win,
        game_status
    from rays_perspective
    left join venues using (venue_id)

)

select * from final