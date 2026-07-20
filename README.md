# Rays Analytics

A portfolio learning project building a modern ELT stack around Tampa Bay Rays game data. The goal is to work through every layer of a real analytics engineering stack — ingestion, transformation, semantic layer, orchestration, BI, and AI — using the same tools and patterns used in production environments.

Built for fun and education, not because anyone asked.

---

## Stack

| Layer | Tool |
|---|---|
| Ingestion | dlt |
| Warehouse (local) | DuckDB |
| Warehouse (cloud) | Snowflake |
| Transformation | dbt Core |
| Semantic layer | MetricFlow + Snowflake Semantic Views |
| Orchestration | GitHub Actions cron (Dagster OSS / Prefect explored as a bonus-track upgrade) |
| Observability | Elementary |
| BI | Evidence |
| CI | GitHub Actions |

---

## Data

MLB Stats API — no authentication required. Pulls Tampa Bay Rays game-level data (team ID 139) for the 2022–2026 seasons (~740 completed games; 2026 still in progress and growing run-over-run) and loads it into a star schema: `dim_teams`, `dim_venues`, `fct_games`.

---

## Running locally

```bash
# Clone and install dependencies
git clone git@github.com:dyllyngiles/rays-analytics.git
cd rays-analytics
make setup

# Activate the virtual environment
source .venv/bin/activate

# Load data into local DuckDB
python mlb_pipeline.py --destination duckdb

# Run dbt (from repo root)
make dbt-build
```

You'll need a `~/.dbt/profiles.yml` with `dev`/`dev_duck` targets — see [dbt profile docs](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles). The DuckDB target needs no credentials; the Snowflake `dev` target reads from a gitignored `.env` at repo root via `env_var()`.

---

## Docs

dbt model documentation is published to GitHub Pages:
**[dyllyngiles.github.io/rays-analytics](https://dyllyngiles.github.io/rays-analytics)**

---

## CI

Two-job pipeline on GitHub Actions. Every PR to `main` runs a DuckDB job — installs dependencies, runs `dbt build` against a local DuckDB file, and executes all tests. On merge to `main`, a second Snowflake job runs the same build against the real warehouse using key-pair authentication via GitHub Secrets. Actions are pinned to exact commit hashes (not floating tags) and dependencies are audited against the OSV vulnerability database on every run.
