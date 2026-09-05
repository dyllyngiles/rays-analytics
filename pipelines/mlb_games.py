import argparse
import os
from collections.abc import Iterator
from datetime import date

import dlt
from dlt.extract import DltResource
from dlt.pipeline.helpers import retry_load
from dlt.sources.helpers import requests
from tenacity import Retrying, stop_after_attempt, retry_if_exception, wait_exponential


CURRENT_SEASON = date.today().year
RAYS_TEAM_ID = 139
COMPLETED_STATUSES = {"Final", "Completed Early"}


def get_rays_schedule(season: int) -> list:
    """Pull Rays game schedule for a given MLB season from the Stats API."""
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"teamId": RAYS_TEAM_ID, "season": season, "sportId": 1, "gameType": "R"}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("dates", [])


@dlt.resource(name="games", write_disposition="merge", primary_key="game_pk")
def games(seasons: list[int]) -> Iterator[dict]:
    for season in seasons:
        print(f"Fetching {season} Rays schedule...")
        loaded = 0
        for game_date in get_rays_schedule(season):
            for game in game_date.get("games", []):
                if game["status"]["detailedState"] not in COMPLETED_STATUSES:
                    continue  # skip Scheduled / In Progress / Postponed
                loaded += 1
                yield {
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
                }
        print(f"  Loaded {loaded} completed games for {season}")


@dlt.source
def mlb_stats_api(seasons: list[int]) -> DltResource:
    return games(seasons)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--destination", default="duckdb", choices=["duckdb", "snowflake"],
        help="Defaults to duckdb (free, local). Pass --destination snowflake to hit the real warehouse.",
    )
    parser.add_argument(
        "--seasons", nargs="+", type=int, default=list(range(2022, CURRENT_SEASON + 1)),
        help="Seasons to (re)load. Defaults to full history through the current season.",
    )
    args = parser.parse_args()

    if args.destination == "duckdb":
        destination = dlt.destinations.duckdb(credentials=os.getenv("DUCKDB_PATH", "dev.duckdb"))
        pipeline = dlt.pipeline(pipeline_name="mlb_games", destination=destination, dataset_name="raw")
    else:
        pipeline = dlt.pipeline(pipeline_name="mlb_games", destination="snowflake", dataset_name="raw")

    for attempt in Retrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=4, max=30),
        retry=retry_if_exception(retry_load()),
        reraise=True,
    ):
        with attempt:
            load_info = pipeline.run(mlb_stats_api(seasons=args.seasons))
    print(load_info)
        