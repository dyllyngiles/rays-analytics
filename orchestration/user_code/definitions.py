from dagster import Definitions
from dagster_dlt import DagsterDltResource, dlt_assets
from pipelines.mlb_games import games_source, games_pipeline


@dlt_assets(
    dlt_source=games_source,
    dlt_pipeline=games_pipeline,
    name="games",
)
def games_dagster_assets(context, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


defs = Definitions(
    assets=[games_dagster_assets],
    resources={"dlt": DagsterDltResource()},
)
