.PHONY: setup dbt-build dbt-debug-ci

setup:
	uv sync --locked

dbt-build:
	uv run --env-file .env dbt build --project-dir rays_analytics

dbt-debug-ci:
	uv run --env-file .env dbt debug --target ci_test --project-dir rays_analytics
