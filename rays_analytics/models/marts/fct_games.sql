with games as (

    select * from {{ ref('stg_games') }}

),

teams as (

    select * from {{ ref('dim_teams') }}

),

venues as (

    select * from {{ ref('dim_venues') }}

),

final as (

    select
        -- ids
        games.game_id,

        -- dates
        games.game_date,
        games.game_started_at,
        games.season,

        -- rays context
        -- game location
        case
            when games.home_team_id = 139 then 'home'
            else 'away'
        end                                             as game_location,

        case
            when games.home_team_id = 139 then 1
            else 0
        end                                             as is_home_game,

        -- opponent
        case
            when games.home_team_id = 139 then games.away_team_id
            else games.home_team_id
        end                                             as opponent_team_id,

        case
            when games.home_team_id = 139 then games.away_team_name
            else games.home_team_name
        end                                             as opponent_team_name,

        -- venue
        games.venue_id,
        games.venue_name,

        -- scores
        case
            when games.home_team_id = 139 then games.home_score
            else games.away_score
        end                                             as rays_runs_scored,

        case
            when games.home_team_id = 139 then games.away_score
            else games.home_score
        end                                             as rays_runs_allowed,

        -- win/loss
        case
            when games.home_team_id = 139 and games.home_score > games.away_score then 1
            when games.away_team_id = 139 and games.away_score > games.home_score then 1
            else 0
        end                                             as rays_win,

        -- game status
        games.game_status

    from games
    left join venues
        on games.venue_id = venues.venue_id

)

select * from final