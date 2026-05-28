#!/bin/bash
set -e

echo "Generating dbt docs..."
cd ~/projects/rays-analytics/rays_analytics
dbt docs generate

echo "Publishing to gh-pages..."
cd ~/projects/rays-analytics
git checkout gh-pages
cp rays_analytics/target/manifest.json .
cp rays_analytics/target/catalog.json .
cp rays_analytics/target/graph_summary.json .
cp rays_analytics/target/run_results.json .
cp rays_analytics/target/semantic_manifest.json .
git add .
git commit -m "Update dbt docs"
git push origin gh-pages
git checkout main

echo "Done! Docs published to https://dyllyngiles.github.io/rays-analytics"