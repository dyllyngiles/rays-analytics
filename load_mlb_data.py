import duckdb
import requests
import os

# Connect to DuckDB
db_path = os.getenv('DUCKDB_PATH', 'dev.duckdb')
con = duckdb.connect(db_path)

# Tampa Bay Rays team ID in the MLB Stats API
RAYS_TEAM_ID = 139

def get_rays_schedule(season: int) -> list:
    """Pull Rays game schedule for a given season."""
    url = f"https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "teamId": RAYS_TEAM_ID,
        "season": season,
        "sportId": 1,
        "gameType": "R"  # Regular season only
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("dates", [])

def load_games(season: int):
    """Extract games from schedule response and load into DuckDB."""
    print(f"Fetching {season} Rays schedule...")
    dates = get_rays_schedule(season)
    
    games = []
    for date in dates:
        for game in date.get("games", []):
            games.append({
                "game_pk": game["gamePk"],
                "game_date": game["gameDate"],
                "season": season,
                "home_team_id": game["teams"]["home"]["team"]["id"],
                "home_team_name": game["teams"]["home"]["team"]["name"],
                "away_team_id": game["teams"]["away"]["team"]["id"],
                "away_team_name": game["teams"]["away"]["team"]["name"],
                "home_score": game["teams"]["home"].get("score"),
                "away_score": game["teams"]["away"].get("score"),
                "status": game["status"]["detailedState"],
                "venue_id": game.get("venue", {}).get("id"),
                "venue_name": game.get("venue", {}).get("name"),
            })
    
    print(f"  Found {len(games)} games")
    
    # Load into DuckDB
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.games (
            game_pk INTEGER PRIMARY KEY,
            game_date VARCHAR,
            season INTEGER,
            home_team_id INTEGER,
            home_team_name VARCHAR,
            away_team_id INTEGER,
            away_team_name VARCHAR,
            home_score INTEGER,
            away_score INTEGER,
            status VARCHAR,
            venue_id INTEGER,
            venue_name VARCHAR
        )
    """)
    
    con.executemany("""
    INSERT INTO raw.games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (game_pk) DO UPDATE SET
        game_date = excluded.game_date,
        season = excluded.season,
        home_team_id = excluded.home_team_id,
        home_team_name = excluded.home_team_name,
        away_team_id = excluded.away_team_id,
        away_team_name = excluded.away_team_name,
        home_score = excluded.home_score,
        away_score = excluded.away_score,
        status = excluded.status,
        venue_id = excluded.venue_id,
        venue_name = excluded.venue_name
""", [list(g.values()) for g in games])
    
    print(f"  Loaded {len(games)} rows into raw.games")

if __name__ == "__main__":
    # Load last 3 seasons
    for season in [2022, 2023, 2024]:
        load_games(season)
    
    # Quick check
    result = con.execute("SELECT season, COUNT(*) as games FROM raw.games GROUP BY season ORDER BY season").fetchall()
    print("\nLoaded data summary:")
    for row in result:
        print(f"  {row[0]}: {row[1]} games")
    
    con.close()
    print("\nDone.")