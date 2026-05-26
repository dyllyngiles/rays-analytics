# CLAUDE.md — rays-analytics

## Project Overview
Portfolio-ready modern ELT stack built for learning and career development.
Rays-focused MLB analytics using MLB Stats API and Statcast data.

## Stack
- Ingestion: dlt
- Warehouse: DuckDB (local, Phase 1) → Snowflake (Phase 3+)
- Transformation: dbt Core with dbt-duckdb adapter
- Orchestration: Dagster OSS or Prefect Cloud (Phase 5)
- Semantic Layer: MetricFlow + Cube (Phase 6)
- BI: Evidence (Phase 6)
- Version Control: GitHub + GitHub Actions

## Environment
- Python 3.12.13 managed by UV
- Virtual environment: .venv (activate with `source .venv/bin/activate`)
- dbt project folder: rays_analytics/

## Conventions
- Branch naming: feature/, fix/, chore/
- Schema naming: TBD
- Model naming: TBD

## Data Sources
- MLB Stats API (no auth required, base URL: https://statsapi.mlb.com/api/v1/)
- Statcast via Baseball Savant (Phase 4+)

## Key Decisions
- UV replaces pip and pyenv
- Docker intentionally excluded
- dbt profiles.yml lives at ~/.dbt/profiles.yml, never committed