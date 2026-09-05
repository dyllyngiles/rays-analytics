# Rays Analytics

A portfolio learning project building a modern ELT stack around Tampa Bay Rays game data. The goal is to work through every layer of a real analytics engineering stack — ingestion, transformation, semantic layer, orchestration, BI, and AI — using the same tools and patterns used in production environments.

Built for fun and education, not because anyone asked.

---

## Stack

**Built and running:**

| Layer | Tool |
|---|---|
| Ingestion | dlt |
| Warehouse (cloud) | Snowflake |
| Transformation | dbt Core |
| Orchestration | GitHub Actions — PR/merge CI gate plus a daily scheduled production pipeline |
| CI | GitHub Actions |

DuckDB is still around, but demoted to an ad hoc local scratchpad — dbt no longer builds against it, only Snowflake.

**Decided, not yet implemented:**

| Layer | Tool | Status |
|---|---|---|
| Observability | TBD | Not yet decided — a scheduled run failing or silently loading bad data isn't yet alerted on |

**Planned (Phase 6+):**

| Layer | Tool |
|---|---|
| Semantic layer | MetricFlow + Snowflake Semantic Views |
| BI | Evidence |

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

# Run dbt against Snowflake (from repo root) — the only dbt build target
make dbt-build

# Optional: load data into a local DuckDB file for ad hoc querying
# (scratchpad only — dbt itself never builds against this)
python pipelines/mlb_games.py --destination duckdb
```

You'll need a `~/.dbt/profiles.yml` with a `dev` target pointed at Snowflake — see [dbt profile docs](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles). It reads from a gitignored `.env` at repo root via `env_var()`. A `dev_duck` target is optional, only needed if you want to query the scratchpad DuckDB file with dbt-adjacent tooling.

---

## Docs

dbt model documentation is published to GitHub Pages:
**[dyllyngiles.github.io/rays-analytics](https://dyllyngiles.github.io/rays-analytics)**

---

## CI and scheduling

Two GitHub Actions workflows, both against Snowflake — no DuckDB in CI.

**`ci.yml`** — every PR to `main` runs a full `dbt build` against a `DEV` schema; merging to `main` runs the same build against `PROD`. Both authenticate via key-pair, with the private key passed inline from a GitHub Secret rather than written to disk. Actions are pinned to exact commit hashes (not floating tags), and dependencies are audited against the OSV vulnerability database on every PR.

**`games_pipeline.yml`** — a daily scheduled workflow (plus manual dispatch) that pulls the current season's games via the dlt pipeline, then runs a full `dbt build` against `PROD`. Guards against overlapping runs with a concurrency lock, and runs `dbt source freshness` as a sanity check before building — not yet a true staleness gate, since the ingestion step it follows always touches the load ledger regardless of whether new data actually showed up.
