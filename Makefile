.PHONY: setup dbt-build dbt-debug-ci dbt-build-duckdb

setup:
	uv sync --locked

dbt-build:
	uv run --env-file .env dbt build --project-dir rays_analytics

dbt-debug-ci:
	uv run --env-file .env dbt debug --target ci_test --project-dir rays_analytics

dbt-build-duckdb:
	uv run --env-file .env dbt build --project-dir rays_analytics --target dev_duck