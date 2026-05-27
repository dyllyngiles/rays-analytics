with source as (

   select * from {{ source('mlb', 'games') }}

),

renamed as (

    select
        -- ids
        game_pk                                    as game_id,

        -- dates
        cast(game_date as timestamp)               as game_started_at,
        cast(game_date as date)                    as game_date,

        -- teams
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,

        -- scores
        home_score,
        away_score,

        -- game context
        status                                     as game_status,
        venue_id,
        venue_name,
        season

    from source

)

select * from renamed