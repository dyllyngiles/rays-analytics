# Phase 5 Retrospective: Dagster OSS on a Self-Hosted VPS — Attempted and Abandoned

**Date:** August 30, 2026
**Branches involved:** `fix/dagster-daemon-workspace-flag` (merged), `phase-5/dagster-assets-and-checks` (uncommitted, to be archived/discarded)
**Outcome:** Self-hosted Dagster on DigitalOcean dropped. Pivoting to GitHub Actions + dbt/dlt native tooling + Elementary.

---

## What this session set out to do

Wire real Dagster assets into the Phase 5 orchestration stack that had been deployed the prior session:
1. Wrap the `games` dlt pipeline as a Dagster asset
2. Generate `@dbt_assets` off `manifest.json`
3. Add the `sources.yml` `asset_key` override for dlt-to-dbt lineage
4. Verify a known Dagster regression (blocked runs incorrectly reporting success) was actually fixed on the current version

None of the four original goals were completed. What actually happened was a much longer chain of infrastructure diagnosis, and it surfaced a hard architectural blocker that wasn't visible until real assets were wired and actually run.

---

## What we found and fixed, in order

### 1. Prior session's "Phase 5 complete" status was inaccurate
CLAUDE.md and CHANGELOG.md both claimed Phase 5 steps 1–6 were done, including "first successful `docker compose up` with all five containers running." In reality:
- `dagster-daemon` was crash-looping on every boot with `No arguments given and no [tool.dagster] block in pyproject.toml found`
- This had gone unnoticed because verification only checked `docker compose ps` (saw "Up") and confirmed the webserver's UI loaded — nobody had read the daemon's own logs
- **Root cause:** `dagster-daemon`'s command in `docker-compose.yml` was missing the `-w /opt/dagster/dagster_home/workspace.yaml` flag that `dagster-webserver`'s command already had. Without it, the daemon defaulted to looking for `workspace.yaml` in its `WORKDIR` (`/opt/dagster`), not `$DAGSTER_HOME` (`/opt/dagster/dagster_home/`), found nothing, and errored.
- **Fixed** via `fix/dagster-daemon-workspace-flag`, merged to `main`. Verified this time by actually watching `docker compose logs dagster-daemon -f` for a sustained, non-crash-looping startup — not just `docker compose ps`.

**Lesson:** "Up" in `docker compose ps` and a working UI are not the same as a working stack. Read every service's own logs before declaring a deployment verified.

### 2. The VPS was on a stale, already-merged-and-deleted branch
`git status` on the VPS showed it was still checked out on `feature/dagster-docker-compose-vps` — a branch CHANGELOG claimed was merged and deleted two weeks prior (PR #35). It also had an uncommitted local diff to `Dockerfile.user_code`.

Investigation revealed the VPS's `origin/main` tracking ref was simply stale — the first `git fetch origin main` that session hadn't actually pulled anything new, and a `2>/dev/null` fallback in an earlier diagnostic command likely masked that. A second, explicit `git fetch origin --prune -v` pulled the real state down, confirmed PR #35 genuinely was merged, and the branch really was gone from GitHub. The VPS's uncommitted `Dockerfile.user_code` diff turned out to be redundant — the same fix already existed in `main` via an earlier commit — so it was safely discarded (`git restore`), and the VPS was moved onto a clean `main` checkout.

**Lesson:** a stale local fetch can make a fully-merged, fully-clean remote state look like unmerged drift. Always do an explicit `--prune -v` fetch before trusting `git log origin/main` on a box that isn't actively worked in day-to-day.

### 3. VPS OS/credential housekeeping detour
Sudo access briefly broke (forgotten local password for `dyllyn`), requiring a DigitalOcean console root-password reset, then setting `dyllyn`'s password from there. Confirmed this didn't reopen any SSH attack surface — `PasswordAuthentication no` and `PermitRootLogin no` in `sshd_config` were unaffected, since local console/account passwords are a separate credential path from network SSH auth. Also ran a routine `apt upgrade` (14 pending packages, no kernel bump, no reboot needed) while in there.

**Lesson:** local account passwords and SSH network auth are separate systems; losing one doesn't compromise the other, but it's worth actually confirming that rather than assuming.

### 4. `mlb_pipeline.py` → `pipelines/mlb_games.py` refactor
To support `dagster-dlt`'s `@dlt_assets` decorator (which needs an importable dlt source/pipeline object, not just CLI-triggered logic), the script was:
- Moved into a new `pipelines/` package (`git mv`), anticipating future pipelines needing a home beyond one flat repo-root file
- Given module-level `games_source`/`games_pipeline` objects, hardcoded to the current season (`date.today().year`) and Snowflake — separate from the existing CLI path, which kept its flexible `--seasons`/`--destination` flags for ad hoc/DuckDB use
- Fixed two real bugs found along the way: a `destination`/`pipeline` variable mix-up that would have thrown `NameError` on any `--destination snowflake` CLI run, and a `date` loop-variable shadowing the imported `datetime.date` class
- Cleaned up: dynamic `--seasons` default (was a hardcoded, annually-stale list), stale docstring reference to a predecessor script, added type hints matching the file's existing convention (skipped a hint for `mlb_stats_api()`'s return type per dlt's own docs not doing so either)
- Confirmed via Claude Code's own repo-wide grep that the blast radius of the rename was small and fully handled: `ci.yml`, `README.md`, and three CLAUDE.md references updated; `CHANGELOG.md` deliberately left untouched as a historical record

**Lesson worth keeping:** separating "what does the data" from "how it gets triggered" (CLI vs. orchestrator) is the right shape, and cost little to build. This groundwork remains valid regardless of the orchestration pivot.

### 5. dagster-dlt wiring and credential resolution
Confirmed current `dagster-dbt`/`dagster-dlt` API shapes against live docs before writing code (worth doing given fast-moving library APIs): `@dbt_assets` + `DbtCliResource` unchanged from expectation; `dagster-embedded-elt` is deprecated in favor of the split `dagster-dlt` package, using `@dlt_assets` + `DagsterDltResource` — a better fit than a hand-rolled `@asset` wrapper, since it maps cleanly to dlt's resource model.

Getting this to actually run into Snowflake required three real fixes:
- `dagster-dlt` added to `pyproject.toml`'s dagster extra, `uv.lock` regenerated
- Confirming `pipelines/` was actually importable from inside the `user-code` image (it wasn't, at first — no `COPY` line existed for it; fixed by adding `COPY pipelines/ ./pipelines/` alongside the existing `orchestration/user_code/` copy)
- **Credentials genuinely weren't on the VPS.** The `user-code` container's `env_file: ../.env` was correctly wired, but the VPS's actual `.env` had never been populated with the `DESTINATION__SNOWFLAKE__CREDENTIALS__*` block at all — it only ever existed locally. Worse, once transferred, `PRIVATE_KEY_PATH` pointed at an absolute Mac filesystem path (`/Users/dyllyngiles/.ssh/...`), meaningless inside a Linux container.
- **Fixed properly, not just patched:** rather than a raw `volumes:` bind mount for the private key, used Docker Compose's native `secrets:` construct (works without Swarm since Compose v2) — standardized `/run/secrets/<name>` path, tighter default permissions, explicit per-service opt-in.

**Lesson:** a local dev environment's working credentials do not imply a fresh deployment target has them. This should be a documented, repeatable step (or a secrets manager), not a one-off manual transfer discovered via failure.

### 6. The actual blocker: MLB Stats API rejects DigitalOcean's IP range
Once credentials resolved, the `games` asset materialized — and immediately failed with `406 Client Error: Not Acceptable` calling `statsapi.mlb.com`. This had run cleanly the day before, and ran cleanly again seconds later from a local DuckDB test, ruling out a code regression.

**Isolated methodically:**
- Same code succeeded locally (Mac, home IP) — 135 games loaded, no error
- Raw `curl` from the VPS, no dlt/Python involved at all — still 406, ruling out anything dlt- or Python-specific
- `curl` from the VPS with a spoofed browser `User-Agent` — still 406, ruling out header-based filtering
- `curl` from a GitHub Actions Codespace (Azure IP range) — clean `200`, proving the API itself isn't universally hostile to cloud/datacenter IPs
- `curl` from a **brand-new, never-used DigitalOcean droplet** — still `406`, confirming this is DigitalOcean's IP range broadly being filtered by MLB's CDN (Varnish/Fastly-flavored, per response headers), not a reputation problem specific to the original box

Checked whether MLB has an official, allow-listed developer access path instead of the public unofficial endpoint — confirmed there isn't one for a project at this scale; `statsapi.mlb.com` has no self-service developer program, and every wrapper/tool in this space (including this project) hits the same unofficial, undocumented endpoint.

**Lesson:** an unofficial public API's bot-filtering posture is an external risk that can change without notice, and it's specifically vulnerable to whichever infrastructure provider you happen to be on. This is not a code quality problem and could not have been caught by better code — only by testing the actual deployment target's network path earlier, ideally before building the rest of the orchestration layer on top of it.

---

## The decision

Given a real deadline and a now-confirmed hard constraint (this specific API is unreachable from DigitalOcean, and a fix — a residential/rotating proxy — adds real ongoing cost and a new dependency for a project explicitly scoped to stay low-cost), the call was made to **drop self-hosted Dagster and the VPS entirely** rather than route around the blocker.

**Dropped:**
- Dagster OSS (self-hosted orchestration, asset graph, sensors, daemon)
- The DigitalOcean VPS + five-container Docker Compose stack
- Tailscale sidecar access pattern
- The `@dlt_assets` groundwork in `pipelines/mlb_games.py` built specifically for Dagster import

**Kept:**
- Snowflake (production) / DuckDB (local dev) — unaffected
- dlt for ingestion, now triggered via scheduled GitHub Actions instead of a self-hosted daemon
- dbt for transformation, with `dbt source freshness` filling part of the "did new data actually land" observability gap
- The dbt docs site / `publish_docs.sh` → GitHub Pages pipeline

**Added:**
- A GitHub Actions workflow with explicit job dependencies, replacing what Dagster's asset graph would have handled
- Elementary, as a lightweight dbt-native observability layer, if alerting beyond a red X in Actions is wanted later

**Net effect:** warehouse + ingestion + transformation + self-hosted orchestration + BI → warehouse + ingestion + transformation + BI, with orchestration reduced to whatever structure dbt/dlt/GitHub Actions provide natively, rather than a dedicated engine.

---

## What actually gets carried forward as real learning

Even though the orchestration layer itself is being dropped, this was not wasted time:
- Real, hands-on experience with `dagster-dlt`/`dagster-dbt`'s current API shapes, Dagster's process architecture (webserver/daemon/user-code gRPC server split), and Compose-level debugging of a multi-container stack
- A concrete, defensible story for why a more sophisticated tool was chosen first, what specifically blocked it, and how the scope call was made under a deadline — arguably a stronger interview narrative than either "I used Dagster" or "I used GitHub Actions" would be alone
- Reusable groundwork: the `pipelines/` package structure, the refactored `mlb_games.py` (bugs fixed, seasons logic corrected), and the Compose `secrets:` pattern are all still valid regardless of what orchestrates them
- A sharper instinct, going forward, to test a deployment target's actual network reachability to external dependencies *before* building orchestration logic on top of it

---

## Open items as of end of session

- `pipelines/mlb_games.py`'s module-level `games_source`/`games_pipeline` objects need to be either repurposed for the GitHub Actions workflow or removed — they currently exist only to satisfy `dagster-dlt`'s import requirements
- `dagster`, `dagster-dbt`, `dagster-postgres`, `dagster-dlt` need removing from `pyproject.toml`'s dagster extra, and `uv.lock` regenerated
- `orchestration/` directory (Dockerfiles, `docker-compose.yml`, `definitions.py`) needs an archiving/deprecation decision
- CLAUDE.md's Phase 5 section needs rewriting to reflect the reversal, not silently overwritten
- CHANGELOG.md needs an entry capturing this session's chain of events and the final decision
- Tailscale admin console likely still shows the now-destroyed `rays-dagster` node — worth removing
- The actual GitHub Actions workflow (ingest → build → test) doesn't exist yet
