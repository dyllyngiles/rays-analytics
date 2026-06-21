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
| Semantic layer | MetricFlow + Cube |
| Orchestration | Dagster OSS or Prefect |
| Observability | Elementary |
| BI | Evidence |
| CI | GitHub Actions |

---

## Data

MLB Stats API — no authentication required. Pulls Tampa Bay Rays game-level data (team ID 139) for the 2022–2024 seasons (486 games) and loads it into a star schema: `dim_teams`, `dim_venues`, `fct_games`.

---

## Running locally

```bash
# Clone and install dependencies
git clone git@github.com:dyllyngiles/rays-analytics.git
cd rays-analytics
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Load data
python load_mlb_data.py

# Run dbt
cd rays_analytics
dbt build
```

You'll need a `~/.dbt/profiles.yml` pointing at a local DuckDB file. See [dbt profile docs](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles).

---

## Docs

dbt model documentation is published to GitHub Pages:
**[dyllyngiles.github.io/rays-analytics](https://dyllyngiles.github.io/rays-analytics)**

---

## CI

Two-job pipeline on GitHub Actions. Every PR to `main` runs a DuckDB job — installs dependencies, runs `dbt build` against a local DuckDB file, and executes all tests. On merge to `main`, a second Snowflake job runs the same build against the real warehouse using key-pair authentication via GitHub Secrets. Actions are pinned to exact commit hashes (not floating tags) and dependencies are audited against the OSV vulnerability database on every run.
