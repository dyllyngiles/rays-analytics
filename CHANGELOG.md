# Changelog

Session-by-session build log for Rays Analytics. For current stack/state/next-actions, see CLAUDE.md.

---

### 2026-08-16 — Phase 5: VPS provider decision

Walked through the VPS provider decision live rather than defaulting to Hetzner as previously assumed. Findings:

- Hetzner's US region pricing (Ashburn) is actually the most expensive option checked, not the cheapest — the EU reputation doesn't hold for US-hosted instances.
- A live DRAM/memory shortage (AI datacenter demand pulling global supply) is pushing up pricing across the board right now — Hetzner took a ~37% hike in April 2026, Raspberry Pi 5 pricing jumped from ~$70 to $85-125 in two months, and AWS/Azure/GCP are expected to follow with smaller increases in H2 2026. Ruled out the Raspberry Pi self-host idea on cost for this reason.
- Considered and rejected: Oracle Cloud Always Free (capacity/signup risk not worth the time cost), Contabo (viable, ~$5-7/mo, but chose reliability over marginal savings), Fly.io/Railway/Render/Cloud Run (wrong architectural shape — built for scale-to-zero, not an always-on Dagster daemon), AWS EC2 free trial (time-boxed to Dec 31 2026, not a real long-term option).
- Re-examined self-hosting on the Mac Mini one more time before closing the door for good. Root-caused the actual blocker as the FileVault/auto-login unattended-reboot conflict — see CLAUDE.md gotchas. Confirmed the door stays closed.
- Decision: DigitalOcean, NYC3, Basic 2vCPU/4GB Droplet, dedicated SSH key. Rationale tied to timeline as much as architecture — season ends October 2026, so this VPS has a ~2-month intentional runway. Optimized for least friction over marginal monthly savings given that horizon, rather than the multi-year cost analysis the earlier provider comparisons implied.

Next: droplet provisioning + SSH hardening (non-root user, ufw, key-only auth).

---

### 2026-08-16 — Phase 5: droplet provisioned and hardened

Droplet stood up on the DigitalOcean plan decided earlier this session: SSH key pair generated, droplet provisioned, connectivity confirmed, then hardened (non-root user, key-only auth, ufw).

Next: install Docker + Docker Compose, stand up the four-service Compose stack + Tailscale sidecar.

---

### 2026-08-18 — Phase 5: VPS build, steps 1–6, first successful Dagster stack boot

Continued from the droplet-provisioned-and-hardened session above, working straight through the locked build order (SSH key → droplet → hardening → Docker/Compose → four-service stack + Tailscale sidecar) to a first successful `docker compose up`. All five containers — `postgres`, `user-code`, `dagster-webserver`, `dagster-daemon`, `tailscale` — came up clean; the Tailscale sidecar joined the tailnet (`rays-dagster` visible in the admin console).

Two real gotchas hit and fixed along the way:

- **Tailscale sidecar needs explicit kernel networking.** The default `TS_USERSPACE` is enabled (userspace mode), which doesn't transparently extend to a sibling container attached via `network_mode: service:tailscale` — the webserver container couldn't reach the tailnet through it. Fix: explicit `TS_USERSPACE: "false"`, `/dev/net/tun` device mount, and `SYS_MODULE` added to `cap_add` in the Tailscale service definition.
- **Build context path mismatch in `Dockerfile.user_code`.** The build context is repo root (`..`), not `orchestration/` — needed so the image can see `pyproject.toml`/`uv.lock` at the root. That means `COPY` paths for anything under `orchestration/` need the `orchestration/` prefix, easy to miss since the repo-root files copied earlier in the same Dockerfile don't need it. `COPY user_code/ ./user_code/` failed on the VPS; fixed to `COPY orchestration/user_code/ ./user_code/`. Fixed directly on the VPS first, then ported back into the repo and committed here.

**New gotcha, worth its own note — Claude Code reads `.env` directly when generating config that references it.** Confirmed this session: while adding Postgres credentials to the Compose stack, Claude Code read and edited `.env` unprompted, pulling its contents into that session's context. Mitigation going forward: explicit "don't touch `.env`" instructions per task. Anything it touched this session should be treated as exposed — `TS_AUTHKEY` was rotated as a result.

**Also worth a line:** `orchestration/` was left uncommitted after Claude Code generated it earlier in the session — caught by a `git status` check before it caused confusion, but a reminder to verify a commit actually landed rather than assume a `git push` shipped everything expected. The same uncommitted batch included `pyproject.toml`/`uv.lock`'s Dagster-extras restructuring (from the dependency-groups-vs-extras research) — now resolved along with everything else in the batch.

Still open: Dagster UI reachability over the tailnet hasn't been manually verified end-to-end yet (browser test still pending). No real assets wired up yet — `definitions.py` is still the empty placeholder. `games` dlt pipeline and `@dbt_assets` off `manifest.json` not yet added.

Next: verify Dagster UI access via Tailscale from a browser, then wrap the `games` dlt pipeline as a Dagster asset.

---

## Extended rationale for settled architectural decisions

Full reasoning and alternatives-considered detail for decisions CLAUDE.md now only summarizes in 1–2 sentences.

**Why S3 + Iceberg + Snowflake Open Catalog over self-hosted Polaris or AWS Glue (decided June 2026; rescoped to bonus track):** Adding a bronze layer — raw data landing in S3 as Iceberg tables instead of being loaded directly into Snowflake — decouples storage from compute. Snowflake and DuckDB can both read the exact same physical files without separate load steps, extending the dbt-portability thesis (swap transformation engines, same SQL) to the storage layer (swap query engines, same data). Three catalog options were weighed:
- **Self-hosted Apache Polaris** — full control, fully open-source, but introduces a server only reachable from the Mac Mini. This breaks CI: GitHub Actions runners can't reach a catalog running on a laptop.
- **AWS Glue** — zero-ops, matches the AWS dependency already accepted via S3, and the market-leading catalog by adoption. But it's proprietary, and doesn't extend the open-source-first preference (dbt Core, Iceberg, OSI) the way Polaris does.
- **Snowflake Open Catalog** — won. It's a managed hosting of the *actual* open-source Apache Polaris (same software, same principal/role model), free during the current billing period (0.5 credits/million requests after — negligible at hobby scale), and reachable by both local dev and CI since it's not self-hosted.

Self-hosted Polaris isn't rejected, just deferred — since Open Catalog runs the identical software, switching to self-hosting later (for the hands-on "I ran this myself" experience) costs little beyond re-registering a handful of tables and re-pointing engine configs. Whichever catalog is active, only one should ever write to a given S3 location — never register the same Iceberg table in two catalogs simultaneously. This entire decision now lives in the bonus track — core Phase 4 writes dlt straight into Snowflake `RAW`, no bronze layer, to keep the application timeline unblocked. The architecture and reasoning stand for whenever the bonus-track work resumes.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow YAML is the OSI v1.0 reference implementation — learning it now means learning the emerging industry standard for semantic layers. Cube provides the API exposure layer that dbt Cloud would otherwise lock behind $100/month. The combination covers the full workflow at zero cost.

**Why Dagster OSS or Prefect over Dagster Cloud:** Dagster Cloud removed free credits from Solo and Starter plans May 1, 2026 — every asset materialization is now billed from zero at ~$0.035–0.040/credit with no grandfathering. Dagster OSS running locally as a Python process, or Prefect Cloud free Hobby tier (2 users, 5 workflows, 500 minutes serverless compute, no credit card required), covers the same learning goals.

**dlt resource design for `games` — completed games only, no live/in-progress state (decided June 2026):** The MLB Stats API schedule endpoint returns every game for a season regardless of status — `Scheduled`, `In Progress`, `Final`, etc. The `games` resource filters to `Final`/`Completed Early` only before yielding, so unplayed or in-progress games never reach `raw.games`. This was a deliberate scope call, not a technical limitation: landing live game state would require loosening `not_null` tests on score columns, expanding `accepted_values` on `game_status`, and rethinking how `rays_win` behaves for a game with no result yet. None of that was judged worth it for the core path — the resource always re-pulls the full current season on every run, so a game picked up as `Final` for the first time merges in cleanly the moment it's actually decided, with no half-loaded intermediate state ever touching the table.

**Why `games` doesn't use dlt's `incremental()` cursor (decided June 2026):** dlt's `dlt.sources.incremental()` helper is built for cursor-based filtering — "give me rows where `updated_at` > last-seen-value." The schedule endpoint doesn't have that shape: a 2022 game's result doesn't change, but the endpoint also doesn't expose a true modified-since cursor, and it returns the whole season every call regardless. The actual pattern used instead is full-season re-pull + `merge` write-disposition keyed on `game_pk` — correct for this data's small size and shape, not a missing feature. This will not hold at Statcast scale — pitch-level data has real cursor potential (game date) and re-pulling full history every run isn't viable at that volume.

**`dim_teams`/`dim_venues` deduplication — most-recent-name-wins (decided June 2026):** Both models originally deduped on `(id, name)` as a pair via `union`/`select distinct`. This broke the moment 2025–2026 data entered the table — team and venue names can change over time for the same numeric id (e.g. a team dropping a city name ahead of relocation; ballpark sponsorship renames), producing two rows for one id and failing the `unique` test on `team_id`/`venue_id`. Fixed by ranking rows per id by `game_date desc` (`row_number()` window function) and keeping only the most recent name. Chosen deliberately over two alternatives: always-earliest-name (rejected — shows stale branding) and full slowly-changing-dimension history (rejected for now — more correct but more work than the core path needs; revisit if a future phase actually needs "what was this called in 2022" as a queryable fact).

**Secrets consolidation — single `.env` shared by dbt and dlt, no `.dlt/secrets.toml` (decided July 2026):** The first real `--destination snowflake` run exposed a gap: dlt keeps its own credential store, entirely separate from dbt's `~/.dbt/profiles.yml`, even though both point at the exact same Snowflake account and service user. The naive fix was a `.dlt/secrets.toml` — a second, tool-specific secrets file duplicating values (account identifier, service user, key path, warehouse, role, database) already sitting in `profiles.yml`. Instead, both tools now read from one gitignored `.env` at repo root: dlt via its native `DESTINATION__SNOWFLAKE__CREDENTIALS__*` environment variable convention, and `profiles.yml` via dbt's `env_var()` Jinja function pointed at those exact same variable names. One canonical value per secret, referenced from two places instead of duplicated in two files. GitHub Secrets for CI remain a separate, unavoidable third location — a CI runner can't read a local, gitignored `.env` — so this consolidation is scoped to local dev only and doesn't change the Phase 4 CI blocker. Invocation pattern: `uv run --env-file .env <command>`, which loads the file identically for Python scripts and dbt commands.

---

## Full "ownership gotcha" narrative (Snowflake RBAC)

Bit three times now — twice in Phase 3, once in Phase 4: anything created through the Snowsight UI under your personal session is owned by whatever role that session defaults to. If that's `ACCOUNTADMIN` and `DBT_SERVICE_USER` runs as `SYSADMIN`, `SYSADMIN` has zero automatic access — Snowflake's role hierarchy doesn't flow downward to it. This surfaced as three different error messages for three different object types:
- **Table** (`RAW.GAMES`, loaded via the Catalog UI): `SQL compilation error: Object ... does not exist or not authorized` — Snowflake intentionally won't confirm whether an unauthorized role's target even exists.
- **Warehouse** (`COMPUTE_WH`, owned by `ACCOUNTADMIN`): `No active warehouse selected in the current session` — the dbt-snowflake connector passes `warehouse:` as a connection parameter (an implicit `USE WAREHOUSE`); if the role lacks `USAGE` on it, the connector fails to set it *silently* rather than erroring at connect time. The error only surfaces later, when a query actually needs compute (which is also why a view model succeeded — `CREATE VIEW` is metadata-only — while table models failed immediately after).
- **Schema** (`RAW`, hit in Phase 4 when dlt tried to recreate `GAMES` from scratch after the old table was dropped): `SQL access control error: Insufficient privileges to operate on schema 'RAW'. Your primary role SYSADMIN must have CREATE TABLE granted on SCHEMA RAYS_ANALYTICS.RAW.` A table-level `SELECT` grant doesn't imply schema-level `CREATE TABLE` — reading an existing table and originating a new one in that schema are separate privileges. This one only surfaced once the old `ACCOUNTADMIN`-owned table was gone, since nothing had ever needed to *create* a table in `RAW` before.

---

## Bronze Layer & Iceberg Catalog Notes (full, bonus track)

**Architecture:** raw data lands in S3 (us-east-2, same region as Snowflake) as Iceberg tables, cataloged through Snowflake Open Catalog. Snowflake and DuckDB both read from this same physical location as separate engines — the catalog resolves "what does this table currently look like" for whichever engine asks. See the S3/Iceberg/Open Catalog decision above for the full reasoning on why Open Catalog won over self-hosted Polaris and AWS Glue.

**Setup requirements:**
- `ORGADMIN` role to create the Open Catalog account itself (one-time, org-level action — the one real exception to "ORGADMIN is irrelevant here")
- An S3 bucket in us-east-2, with IAM credentials scoped to it
- A storage configuration in Open Catalog pointing at that bucket

**Cost:** free during the current billing period; 0.5 credits/million requests once billing starts (~$1/million requests at Standard edition rates) — negligible at this project's query volume.

**Single-writer rule:** only one catalog should ever write to a given S3 Iceberg location. Registering the same table in two catalogs (e.g., both Open Catalog and a self-hosted Polaris instance) risks both silently corrupting each other's metadata pointers, since they don't share transaction state.

**Switching catalogs later, if ever needed:** because Iceberg tables are self-describing (metadata files already sit in S3 next to the data), switching catalogs is a re-registration + re-pointing operation, not a data migration — the files never move. At this project's table count (low single digits to maybe a dozen post-Statcast), that's an afternoon of work, not a project. Switching specifically between Open Catalog and self-hosted Polaris is the cheapest direction, since they're the same software with the same principal/role model — only the AWS Glue direction requires learning a genuinely different auth model (plain IAM instead of principals/catalog-roles).

**Self-hosted Polaris status:** deferred, not rejected. If the hands-on "ran the server myself" experience becomes its own pebble worth chasing later, the switch from Open Catalog is low-friction for the reasons above. Lakekeeper (Rust, single-binary, lighter footprint than Polaris's JVM+Postgres) is worth a look as an alternative self-hosting target if/when that day comes — same open-source values fit, less weight on the Mac Mini.

---

## Data Model note

The `MissingArgumentsPropertyInGenericTestDeprecation` warning on the `relationships` test in `models/marts/schema.yml` was fixed in PR #14 (nested arguments under an `arguments:` property, matching the existing `accepted_values` pattern).

## Phase 3 — Real Warehouse: completed items

- Snowflake trial account created — Standard edition, AWS us-east-2 ✅
- Resource Monitor configured — MONTHLY_SPEND_CAP, 15 credits/month, suspend at 100% ✅
- Warehouse configured — COMPUTE_WH, X-Small, 60-sec auto-suspend ✅
- Database and schemas created — RAYS_ANALYTICS with RAW, DEV, PROD ✅
- Service user created — DBT_SERVICE_USER, TYPE = SERVICE, SYSADMIN role ✅
- Key-pair authentication configured — PKCS#8 format, public key registered ✅
- dbt-snowflake v1.11.4 installed ✅
- profiles.yml updated — Snowflake as default dev target, DuckDB retained as dev_duck ✅
- dbt debug passing ✅
- `relationships` test deprecation warning fixed — PR #14 ✅
- UV version corrected to 0.11.17 in docs — PR #15 ✅
- Dual-job CI architecture (DuckDB-every-PR / Snowflake-on-merge) designed and documented, not yet implemented. `ci.yml` on `main` currently has a single DuckDB job triggered on `pull_request` only — no Snowflake job, no GitHub Secrets configured yet. This is real, scoped work, not a doc gap — tracked as a Phase 4 wrap-up item.
- Workload Identity Federation researched and ruled out — unsupported in dbt-snowflake as of June 2026; key-pair auth confirmed correct ✅ **[Revised July 2026, then reverted later in July 2026 — a mid-July session incorrectly believed `dbt-snowflake` had gained WIF support via a PR merged May 20, 2026, and the CI job briefly planned to adopt WIF; a later-July session found `dbt-labs/dbt-adapters` PR #1316 is still open/unmerged, no `dbt-snowflake` release has WIF support, and reversed the plan back to key-pair. This June 2026 finding was correct all along. See Snowflake CI Auth Notes in CLAUDE.md.]**
- `RAYS_ANALYTICS.RAW.GAMES` populated via one-time manual CSV stopgap (486 games) ✅
- Full `dbt build` passing against real Snowflake data — models and all 44 tests ✅
- Snowflake privilege/RBAC gotcha hit and resolved twice (table + warehouse ownership) — see Role Hierarchy notes ✅
- Query Profile explored on a compiled model ✅
- dbt Projects on Snowflake explored (found unconfigured; deliberately deferred to Phase 5 decision) ✅

## Phase 4 — Ingestion: completed items

**Completed this session (June 2026):**
- Phase 3 wrap-up debt cleared: confirmed `DEFAULT_ROLE = SYSADMIN` set on service user; flipped local `profiles.yml` target to `dev_duck`; full `dbt build` passing clean against DuckDB ✅
- `dlt==1.28.1` installed via `uv add "dlt[duckdb,snowflake]"` ✅
- Feature branch `feature/dlt-games-pipeline` created; `load_mlb_data.py` removed via `git rm` ✅
- `mlb_pipeline.py` built at repo root — `games` resource (merge write-disposition, `game_pk` primary key), `mlb_stats_api` source, destination-parameterized via `--destination duckdb|snowflake` CLI arg (defaults to `duckdb` — Snowflake compute only spent when explicitly requested) ✅
- End-to-end DuckDB load verified: 729 completed games across 2022–2026 (2026 partial season, correctly growing run-over-run as games finish) ✅
- `accepted_values` tests on `season` updated to include 2025/2026 in both `staging/schema.yml` and `marts/schema.yml` ✅
- `dim_teams.sql` / `dim_venues.sql` fixed — see dedup decision above ✅
- Full `dbt build` passing clean against DuckDB with dlt-sourced data — 48/48 ✅

**Completed since (July 2026 session):**
- `feature/dlt-games-pipeline` confirmed merged to `main` — the `ci.yml` fix and the real Snowflake load both landed
- Real `--destination snowflake` run succeeded: ~740 completed games loaded into `RAYS_ANALYTICS.RAW.GAMES`, correctly owned by `SYSADMIN`
- Hit and resolved the third RBAC ownership gotcha (schema-level `CREATE TABLE`) — see Role Hierarchy & Privilege Notes
- Secrets consolidated: single `.env` now shared by dbt and dlt for Snowflake credentials, replacing the need for a separate `.dlt/secrets.toml`

**Completed since (July 2026, continued session):**
- Researched current production CI/CD auth patterns: Snowflake WIF reached GA August 2025 and is Snowflake's recommended pattern; `dbt-snowflake` gained WIF support via a PR merged May 20, 2026; dlt's Snowflake destination has no WIF support at all — see Workload Identity Federation (WIF) Notes in CLAUDE.md
- Decided the Snowflake-on-merge CI job adopts WIF instead of key-pair-in-Secrets; dlt keeps its existing `.env` key-pair setup since the CI job doesn't run dlt (yet) — flagged as a forward-looking asymmetry for Phase 5
- Re-evaluated and reconfirmed GitHub Actions cron (not Dagster/Prefect) as the Phase 5 scheduler — see the GitHub Actions cron reliability decision in CLAUDE.md's Key Architectural Decisions
- Completed the Snowflake-side WIF setup in Snowsight (no branch needed) — `RAYS_ANALYTICS_CI_SERVICE` user, `SYSADMIN` role grant, OIDC authentication policy scoped to `repo:dyllyngiles/rays-analytics:ref:refs/heads/main`; confirmed via `DESCRIBE USER` and `INFORMATION_SCHEMA.POLICY_REFERENCES`
- Hit and resolved three new WIF-specific gotchas (`DEFAULT_ROLE` not auto-granting, `CREATE AUTHENTICATION POLICY` needing a schema-level grant, `ALTER USER ... SET AUTHENTICATION POLICY` taking no `=`) — full detail in Workload Identity Federation (WIF) Notes, CLAUDE.md

---

## Session Handoff Log

**Last session:**
- Confirmed `fix/relationships-test-deprecation` (PR #14) and `docs/update-uv-version` (PR #15) were already merged via `git log main..<branch>` — both showed empty diffs, confirming full merge. Cleaned up local branches; remote branches were already auto-deleted by GitHub on merge.
- Set `git config --global fetch.prune true` going forward.
- Re-evaluated and confirmed the DuckDB-local/Snowflake-production split: it's already encoded in the CI dual-job architecture (DuckDB on every PR, Snowflake on merge). No new "Phase 3.5" needed — just a Phase 3 wrap-up item (flip local default target to `dev_duck`, not yet done) and a Phase 4 design decision (dlt dual destinations, decoupled cadence — see Phase 4 notes).
- Deferred MotherDuck (work-related interest, not this project) and the weekly financials report idea (work-related only, not Rays Analytics scope).
- Closed out remaining Phase 3 checklist:
  - Loaded `RAW.GAMES` via one-time manual CSV stopgap from DuckDB
  - Hit and resolved two separate Snowflake RBAC gotchas (table grant, then warehouse grant) — both caused by objects created under `ACCOUNTADMIN` via the Snowsight UI not being accessible to `SYSADMIN` (the role `DBT_SERVICE_USER` runs as)
  - Full `dbt build` passing against Snowflake with real data, row counts verified correct
  - Decided `SYSADMIN` as default Snowsight role going forward; `ACCOUNTADMIN` reserved for account-level tasks only
  - Explored Query Profile — found partition pruning lives in the Statistics pane (whole-query view, or per-table by selecting a TableScan node); trivial at this data volume since everything fits in one micro-partition
  - Explored dbt Projects on Snowflake — found unconfigured, requires GitHub API integration + Git-connected Workspace to set up; deliberately deferred to the Phase 5 orchestration decision
  - Caught and corrected a Snowsight navigation drift from training data (Database Explorer now under Catalog, dbt Projects now under Transformation)
- Phase 3 marked complete.

**Active branch:** `main` (clean; `fix/relationships-test-deprecation` and `docs/update-uv-version` deleted locally after confirming merge)

**Decisions made this session not captured elsewhere:**
- No new phase number for "DuckDB-first dev workflow" — it's a discipline applied within Phase 4, not a separate phase
- Two-role default for day-to-day Snowsight use (`SYSADMIN` default, `ACCOUNTADMIN` for account-level only) — full four-role rotation judged as enterprise ceremony not worth it solo
- Snowflake Optima Metadata (automatic pruning metadata for high-frequency query patterns) noted as existing but not relevant at current hobby-project query volume

---

**Session (June 2026) — Phase 4 dlt pipeline, `games` resource built end-to-end:**
- Cleared remaining Phase 3 wrap-up debt: confirmed `DEFAULT_ROLE = SYSADMIN`; flipped local `profiles.yml` target to `dev_duck`; full `dbt build` verified passing clean against DuckDB (hit and fixed the classic relative-`DUCKDB_PATH` decoy-file bug along the way — see Local Environment notes in CLAUDE.md)
- Installed `dlt==1.28.1` with `[duckdb,snowflake]` extras; confirmed via `pyproject.toml`, not just a clean install message
- Created `feature/dlt-games-pipeline`; removed `load_mlb_data.py` via `git rm`; built `mlb_pipeline.py` from scratch — `games` resource (merge write-disposition, `game_pk` primary key, completed-games-only filter), `mlb_stats_api` source, `--destination duckdb|snowflake` CLI flag (default `duckdb`)
- Hit and resolved the dlt table-ownership collision (pre-existing `raw.games` table from the old manual loader couldn't accept dlt's tracking columns) — deleted `dev.duckdb`, let dlt recreate the table cleanly
- End-to-end verified: 729 completed games loaded across 2022–2026, confirmed live by re-running minutes apart and watching the 2026 count tick up as real games finished
- Hit, diagnosed, and fixed two real test failures the larger dataset surfaced: `accepted_values` on `season` (needed 2025/2026 added — mechanical fix), and `unique` failures on `dim_teams`/`dim_venues` (real cause — team/venue renames over time; user independently verified the Athletics name change in `stg_games` directly via DuckDB CLI before accepting the fix)
- Full `dbt build` passing 48/48 against dlt-sourced DuckDB data
- Installed DuckDB CLI (`brew install duckdb`) as the preferred path for ad hoc local queries — user doesn't use DBeaver day-to-day despite it being installed
- **Found and corrected a real documentation/reality gap:** CLAUDE.md's Phase 3 checklist and CI Architecture Notes both claimed a dual-job (DuckDB + Snowflake) CI setup with GitHub Secrets already configured. Actual `ci.yml` on `main` only has a single DuckDB-only job. Corrected throughout the doc — see CI Architecture Notes and Phase 4 in CLAUDE.md.

**Decisions made this session, not fully captured in Part 1 prose:**
- `games` resource deliberately excludes Scheduled/In Progress games — completed-games-only is the chosen scope for the core path, not a placeholder
- `games` does not use `dlt.sources.incremental()` — full-season re-pull + merge fits this source's shape better; the real incremental cursor pattern is deferred to Statcast, where it'll actually be needed
- dlt pipeline destination is a CLI flag, not hardcoded, specifically so DuckDB can be refreshed freely (real data, zero cost) independent of Snowflake spend
- `dim_teams`/`dim_venues` use most-recent-name-wins (ranked by `game_date desc`) rather than full SCD-style history tracking — simplest correct option for the core path, revisit only if a future phase needs historical name lookups

**Active branch (as of that session):** `feature/dlt-games-pipeline` — since confirmed merged to `main` (see the July 2026 session below). Three known blockers at the time:
1. `ci.yml`'s DuckDB job still calls deleted `load_mlb_data.py` — needs to call `mlb_pipeline.py --destination duckdb` — **resolved before merge**
2. Snowflake `RAW.GAMES` still has the Phase 3 manual-CSV-stopgap table; first `--destination snowflake` run will hit the same table-ownership collision DuckDB hit — needs the table dropped first — **resolved in the July 2026 session below**
3. CI's Snowflake-on-merge job doesn't exist yet (secrets + second job definition + push-trigger) — currently scoped as its own follow-up session, not a quick add-on — **still open, see CI Architecture Notes in CLAUDE.md**

When Phase 6 starts: decide Lightdash vs. Metabase vs. keeping Cube+Evidence for the internal self-serve BI question.

---

**Session (July 2026) — Real Snowflake load, secrets consolidation, third RBAC gotcha:**
- Confirmed `feature/dlt-games-pipeline` was merged to `main` at some point after the last documented session — `ci.yml` already correctly calls `mlb_pipeline.py --destination duckdb`, and `mlb_pipeline.py` exists on `main`. Blocker #1 above was already resolved; the "Known open items" list just hadn't been updated to reflect it.
- Dropped the Phase 3 manual-CSV-stopgap `RAYS_ANALYTICS.RAW.GAMES` table (owned by `ACCOUNTADMIN`) to let dlt recreate it cleanly, owned by `SYSADMIN` this time
- Hit the Snowflake credentials gap for dlt (a separate config store from dbt's `profiles.yml`). Instead of adding a `.dlt/secrets.toml`, consolidated to a single `.env` at repo root, read natively by both dlt (`DESTINATION__SNOWFLAKE__CREDENTIALS__*` env vars) and dbt (`profiles.yml` via `env_var()`) — see secrets consolidation decision above
- Hit and resolved the third instance of the `ACCOUNTADMIN`/`SYSADMIN` ownership gotcha, this time at the schema level (missing `CREATE TABLE` privilege on `SCHEMA RAW`) — see full ownership gotcha narrative above
- Real `--destination snowflake` run succeeded: ~740 completed games loaded into `RAYS_ANALYTICS.RAW.GAMES`, verified via `INFORMATION_SCHEMA.TABLES` (owner now `SYSADMIN`, row count and season range confirmed)

**Active branch:** `chore/consolidate-secrets-env` — not yet merged. Both the `.env` file and the `profiles.yml` edit live outside the repo (gitignored / outside version control by design), so this branch's only actual diff was the CLAUDE.md update.

**Next actions (superseded below — see "Session (July 2026, continued)" for the current list).**

---

**Session (July 2026, continued) — WIF research, orchestration re-evaluation, Snowsight setup for CI job:**
- Researched current (July 2026) production patterns before building the Snowflake-on-merge CI job. Findings: Snowflake WIF reached GA August 2025 and is Snowflake's recommended CI/CD auth pattern; `dbt-snowflake` gained WIF support via a PR merged May 20, 2026; dlt's Snowflake destination has no WIF support at all (password/key-pair/OAuth/Snowpark-OAuth-token only) — see Workload Identity Federation (WIF) Notes in CLAUDE.md for full detail.
- **Decided:** the Snowflake-on-merge CI job (dbt-only) adopts WIF instead of key-pair-in-Secrets. dlt stays on its existing `.env` key-pair setup — the CI job doesn't run dlt, so the dlt/WIF gap doesn't block it, but it's now a documented forward-looking gotcha for Phase 5.
- Re-evaluated the Phase 5 orchestration choice given the "get to Statcast fast" priority. **Decided:** keep GitHub Actions cron rather than pulling Dagster OSS/Prefect Cloud forward from the bonus track — the actual risk (a missed incremental run going unnoticed) is cheaply solved by the `dbt source freshness` check already in the Phase 5 core plan, not by adopting a new orchestrator. Confirmed via research that GitHub Actions cron reliability has genuinely degraded in 2026 (scheduler delays worsening since February 2026; a 60-day-no-activity auto-disable that's a real risk during MLB's off-season) — this is why the freshness check + a `workflow_dispatch:` fallback trigger need to land before Statcast ships, not after.
- Refreshed the dbt Core v2.0 status note — still alpha (alpha.4 as of mid-July 2026), dbt Labs targeting GA within months, v1.11.x stays the daily driver until Phase 8 re-evaluation.
- Completed the Snowflake-side WIF setup in Snowsight — no branch needed, pure account config:
  - Created `RAYS_ANALYTICS_CI_SERVICE` (`TYPE = SERVICE`, `WORKLOAD_IDENTITY` block scoped to `repo:dyllyngiles/rays-analytics:ref:refs/heads/main`) — required `SECURITYADMIN`, not `SYSADMIN` (see the domain-split note in Role Hierarchy & Privilege Notes, CLAUDE.md)
  - Hit and resolved three new gotchas along the way: `DEFAULT_ROLE` not auto-granting (needed explicit `GRANT ROLE SYSADMIN TO USER ...`), `CREATE AUTHENTICATION POLICY` needing a schema-level grant (`RAW` is `SYSADMIN`-owned), and `ALTER USER ... SET AUTHENTICATION POLICY` taking no `=` — all captured in WIF Notes, CLAUDE.md
  - Confirmed via `DESCRIBE USER` (`HAS_WORKLOAD_IDENTITY: true`) and `INFORMATION_SCHEMA.POLICY_REFERENCES` (auth policy attachment isn't visible in `DESCRIBE USER` output at all)

**Active branch:** new branch being opened for the `ci.yml` changes (not yet named as of that handoff) — superseded by `chore/split-claude-md-changelog` this session, see below.

**Next actions (as of that session):**
1. Open/name the feature branch for `ci.yml` changes
2. Add the second CI job: `push`-to-`main` trigger, `permissions: id-token: write`, OIDC-token-fetch step, dynamic Snowflake `profiles.yml` generation using non-secret identifiers + `authenticator: workload_identity`
3. Confirm and pin the exact `dbt-snowflake` version that shipped WIF support
4. Merge, closing out the last Phase 4 blocker
5. Before starting Statcast: add the `dbt source freshness` check/alert and `workflow_dispatch:` fallback trigger to the cron job

---

**Session (July 2026) — Split CLAUDE.md into current-state doc + this CHANGELOG.md:**
- CLAUDE.md had grown to ~75k characters, past Claude Code's 40k-char limit, mixing current-state reference with session-by-session narrative history. Split per `scratch/claude-md-split-instructions.md`: this CHANGELOG.md now holds the full session log, extended architectural-decision rationale, the full RBAC ownership-gotcha narrative, the full Bronze Layer/Iceberg Catalog section, and the Phase 3/4 "completed this session" bullet lists. CLAUDE.md keeps current-state/operational content, the full WIF reasoning and setup (still actively relevant — `ci.yml` work isn't done), and a short "Current Status" section pointing here for history.

---

**Session (July 2026) — WIF→key-pair reversal, `.env`/`--project-dir` structural fix, Snowflake CI job:**
- Before writing the `ci.yml` Snowflake job planned in the prior session, re-verified the WIF prerequisite instead of taking the earlier research at face value. The earlier claim — "`dbt-snowflake` gained WIF support via a PR merged May 20, 2026" — didn't hold up: `dbt-labs/dbt-adapters` PR #1316 ("Adding support for Snowflake Workload Identity Federation") is still **open**, open since September 2025, blocked on a maintainer requirement for ongoing integration-test infrastructure before merge. No stable or pre-release `dbt-snowflake` version ships WIF support as of this session. The dbt-snowflake v1.12.0 milestone tracker shows the work at 45% complete.
- **Decided: reversed the CI auth plan from WIF back to key-pair.** This removes the asymmetry the earlier plan had accepted (dbt secretless via WIF, dlt still needing key-pair) — both tools now use key-pair, matching. Full current-state reasoning: see Snowflake CI Auth Notes in CLAUDE.md (renamed from Workload Identity Federation (WIF) Notes).
- Generated and registered a new key-pair for `RAYS_ANALYTICS_CI_SERVICE` (`RSA_PUBLIC_KEY` had never been set — the account was created straight for WIF and had no key material). Left the `WIF_GITHUB_ONLY` authentication policy attached rather than removing it — its `ALLOWED_PROVIDERS = (OIDC)` restricts *which* IdP a workload-identity login could use, but doesn't block key-pair logins, since `AUTHENTICATION_METHODS` on the policy is `[ALL]`. Verified via `dbt debug --target ci_test` against a temporary `ci_test` target in `~/.dbt/profiles.yml`, then removed that target once confirmed.
- Separately, hit and fixed a structural gap while wiring up local/CI parity: dbt v1.12's native `.env` autoload is CWD-bound with no `--project-dir` support, and this repo's `.env` lives at repo root while `dbt_project.yml` lives in `rays_analytics/` — the native autoload was never going to fit this layout even after upgrading. Fixed with a repo-root `Makefile` (`make setup`, `make dbt-build`, `make dbt-debug-ci`) wrapping `uv run --env-file .env dbt ... --project-dir rays_analytics`, replacing the `cd rays_analytics` convention. See Workflow Conventions in CLAUDE.md.
- Added the second `ci.yml` job (`push`-to-`main`, key-pair auth, no `id-token: write` since key-pair doesn't use OIDC) — closes the last open Phase 4 blocker. See CI Architecture Notes in CLAUDE.md.
- Flagged a follow-up, not done this session: the CI job runs under `SYSADMIN`, broader than it needs. A scoped `CI_DEPLOYER` role is a known next step, deprioritized behind the README/walkthrough and a baseball-question mart.

**Preserved for history — the original WIF `CREATE USER`/OIDC Snowsight setup SQL** (removed from CLAUDE.md's now-renamed Snowflake CI Auth Notes section, since the account no longer authenticates this way, but the account-side config itself was left in place dormant rather than torn down):
```sql
USE ROLE SECURITYADMIN;

CREATE USER RAYS_ANALYTICS_CI_SERVICE
  TYPE = SERVICE
  WORKLOAD_IDENTITY = (
    TYPE = OIDC
    ISSUER = 'https://token.actions.githubusercontent.com'
    SUBJECT = 'repo:dyllyngiles/rays-analytics:ref:refs/heads/main'
  )
  DEFAULT_ROLE = SYSADMIN;

GRANT ROLE SYSADMIN TO USER RAYS_ANALYTICS_CI_SERVICE;

-- Authentication policy requires CREATE AUTHENTICATION POLICY on the target schema;
-- RAW is owned by SYSADMIN, so SECURITYADMIN needed an explicit grant first:
-- (run as SYSADMIN) GRANT CREATE AUTHENTICATION POLICY ON SCHEMA RAYS_ANALYTICS.RAW TO ROLE SECURITYADMIN;

CREATE AUTHENTICATION POLICY RAYS_ANALYTICS.RAW.wif_github_only
  WORKLOAD_IDENTITY_POLICY = (
    ALLOWED_PROVIDERS = (OIDC)
    ALLOWED_OIDC_ISSUERS = ('https://token.actions.githubusercontent.com')
  );

ALTER USER RAYS_ANALYTICS_CI_SERVICE
  SET AUTHENTICATION POLICY RAYS_ANALYTICS.RAW.wif_github_only;
```

Confirmed at the time via `DESCRIBE USER RAYS_ANALYTICS_CI_SERVICE` (`HAS_WORKLOAD_IDENTITY: true`) and:
```sql
SELECT * FROM TABLE(
  INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME => 'RAYS_ANALYTICS_CI_SERVICE',
    REF_ENTITY_DOMAIN => 'USER'
  )
);
```

**Active branch:** `fix/ci-snowflake-key-pair-auth`

**Next actions (as of this session):**
1. Merge `fix/ci-snowflake-key-pair-auth`, closing Phase 4's last blocker
2. Scope the CI job's Snowflake role down from `SYSADMIN` to a dedicated `CI_DEPLOYER` role
3. Before Statcast: add the `dbt source freshness` check/alert and `workflow_dispatch:` fallback trigger to the cron job
4. Begin the Statcast/pybaseball resource
5. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence

Note: `chore/split-claude-md-changelog` remains a separate open branch, not touched this session.

---

**Session (July 2026) — Phase 5 orchestration decision: Dagster OSS, self-hosted:**
- Researched the Phase 5 orchestration question in depth, comparing four candidates: Dagster OSS (self-hosted), Prefect Cloud Hobby tier, Prefect OSS (self-hosted), and Kestra. Kestra ruled out early — less Python-native, weaker fit for the dbt-model-as-asset workflow this project wants. Prefect Cloud Hobby ruled out on the same "external vendor with a free tier that can change terms" grounds that already sank Dagster Cloud (see the Dagster Cloud pricing decision above) — self-hosting was preferred over any hosted free tier at this point.
- Landscape context surfaced mid-research: Prefect acquired Dagster Labs, announced July 13, 2026; the combined company operates under the Prefect name starting August 2026. Both products currently keep their name, license (Apache 2.0), and roadmap per official statements, and Dagster founder Nick Schrock has departed. Noted as a footnote in CLAUDE.md's Key Architectural Decisions — affects long-term vendor-risk framing but didn't change the decision itself, since both remaining candidates (Dagster OSS, Prefect OSS) are Apache 2.0 and self-hostable regardless of which corporate entity stewards them.
- **Decided: Dagster OSS, self-hosted on the Mac Mini (kept powered on), no Docker.** Chosen over Prefect OSS for: stronger comp/market signal specifically for DE-adjacent AE roles at smaller/mid-market companies; more Python surface area (assets, resources, IO managers vs. Prefect's simpler flow/task decorators) judged more valuable to learn; and `dagster-dbt` auto-generates one asset per dbt model straight from `manifest.json`, preserving the existing dbt DAG with no remodeling needed. Dagster OSS defaults to SQLite for run/event storage, with `dagster-webserver` and `dagster-daemon` running as plain Python processes under `DAGSTER_HOME` — fits the no-Docker, 16GB-RAM constraints already governing this stack. Fully self-hosted, so no new vendor-pricing risk from the acquisition news above.
- **Corrected a data-loss framing error from the prior (July 2026, continued) session.** That session's GitHub Actions cron decision reasoned that a missed/failed scheduled run risked a "silent watermark gap" once Statcast's real incremental cursor was in play — this was overstated. As long as the incremental cursor state is stored durably (dlt already does this via pipeline state) and write-disposition is `merge` on a stable key, a missed run just means the next successful run pulls a larger window and self-heals; Baseball Savant/Statcast data doesn't expire, so there's no source-side retention risk. The GitHub Actions cron reliability concerns from that session (scheduler delays since February 2026, 60-day-inactivity auto-disable) were real research findings, but Dagster is **not** being adopted for data-safety reasons — it's chosen for long-term architecture, extensibility, and career-signal reasons. CLAUDE.md's Key Architectural Decisions section now carries this correction directly rather than leaving the original overstated framing standing.
- **Finalized Phase 5 scope**, replacing the GitHub-Actions-cron-centric plan:
  - Wrap the existing dlt `games` pipeline as a Dagster asset
  - Generate dbt model assets via `@dbt_assets` off `manifest.json`
  - Freshness checks via Dagster asset checks (configurable from dbt `meta` config in `schema.yml`), replacing the standalone `dbt source freshness` task previously planned
  - Alerting: email over Slack — simpler for a solo project, already reaches phone via Mail push, no new account/app to check. Elementary is no longer a Phase 5 dependency now that Dagster's own asset checks + sensors cover freshness alerting natively; Elementary remains a possible separate future decision for dbt-test-specific anomaly detection/reporting beyond what Dagster gives.
  - Dagster's schedule replaces GitHub Actions cron for *production* runs specifically — GitHub Actions keeps its existing role as the PR/merge-time code-correctness gate (DuckDB build on PRs, Snowflake build on merge) unchanged.
  - `workflow_dispatch:` fallback and the GH Actions dead-man's-switch concern are no longer needed for the scheduling mechanism itself, since Dagster's daemon isn't dependent on GitHub's scheduler. New consideration in its place: a `launchd` LaunchAgent so the Dagster daemon survives Mac reboots automatically. Extended Mac downtime (a different failure mode from a quick reboot) is still a real concern — self-heals for `games` (full re-pull pattern) but would not self-heal once Statcast uses a true incremental cursor, same as a missed GH Actions run wouldn't have. An external heartbeat/dead-man's-switch is still a reasonable future addition, just decoupled from the orchestrator choice now.
- **New gap identified, not yet resolved:** even with Dagster running, there's currently no alerting for "run succeeded but data is wrong" (e.g., a clean run that pulled zero games, or stale/duplicate data) — only hard failures trigger a notification today. Requires actively writing freshness/volume/quality checks once Dagster is up; doesn't come for free with the migration. Flagged in CLAUDE.md's Phase 5 section as a known open item, not urgent.
- Estimated setup time: 6–9 hours, likely spanning multiple sessions rather than one sitting.
- Updated CLAUDE.md's stack table: Dagster OSS is now the selected Phase 5 orchestration tool, superseding the earlier "GitHub Actions cron, under re-evaluation" status; Observability row updated to reflect Dagster asset checks over Elementary for Phase 5 freshness alerting.

**Active branch:** `docs/update-claude-md-phase5-orchestration-decision` — docs-only, no code changes. Same pattern as `docs/update-claude-md-phase4-complete` (PR #27).

**Next actions:**
1. Set up Dagster OSS locally (`dagster-webserver` + `dagster-daemon` under `DAGSTER_HOME`) and a `launchd` LaunchAgent for reboot survival
2. Wrap the `games` dlt pipeline as a Dagster asset; generate dbt model assets via `@dbt_assets` off `manifest.json`
3. Add Dagster asset checks for freshness (from dbt `meta` config) and email alerting
4. Begin the Statcast/pybaseball resource — first real test of dlt's `incremental()` cursor pattern
5. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence

---

**Session (August 2026) — README/CLAUDE.md sync, built-vs-planned clarity, `make dbt-build-duckdb`:**
- Added a `dbt-build-duckdb` Makefile target (mirrors `dbt-build`, targets `dev_duck`) so local DuckDB refreshes don't need the full dbt invocation typed out — committed on `chore/add-dbt-build-duckdb-target`.
- Found README.md had drifted from CLAUDE.md/CHANGELOG.md: it still listed "GitHub Actions cron" as the orchestration layer and Elementary as observability, both superseded by the July 2026 Dagster OSS decision.
- **Bigger gap found on a closer pass:** both CLAUDE.md's stack table and README's stack table read as if every listed tool were actually running. Checked `pyproject.toml` and the repo tree directly — only dlt, dbt-core/dbt-snowflake, DuckDB/Snowflake, and GitHub Actions are real today. Dagster is a made decision with zero implementation yet (GitHub Actions cron is still the only scheduler actually executing runs); MetricFlow, Snowflake Semantic Views, and Evidence are Phase 6+ and not started; Marimo had a stale "Added in Phase 4" note in CLAUDE.md despite never being added to `pyproject.toml`.
- Fixed both docs to distinguish status explicitly: CLAUDE.md's stack table gained a **Status** column (Running / Decided-not-implemented / Planned / Bonus-track-not-started); README's single stack table was split into three — Built and running, Decided not yet implemented, Planned (Phase 6+). Corrected the Marimo note in CLAUDE.md in the same pass.
- This CHANGELOG was otherwise current — its Phase 5 decision narrative and Next Actions list already correctly describe Dagster as decided-but-not-started, so no factual correction needed there beyond this entry.

---

**Session (August 2026) — Long Claude.ai architecture session: DuckDB dropped as a build target, orchestration hosting moved off the Mac Mini to a VPS:**

**DuckDB / transformation layer decisions:**
- **Decided: DuckDB dropped as a dbt build target.** dbt now builds only against Snowflake (dev and prod); DuckDB demoted to an ad hoc query scratchpad only (CLI / Marimo), the same non-build role DBeaver was already excluded from. Reasoning: the original multi-engine goal — S3 as home base, swap compute engines freely — never paid for itself at this project's size. It forced permanent dialect-portability discipline (routing everything through `dbt_date` instead of native SQL) and blocked dbt's `ref()` from working normally across a two-engine split. Added Snowflake compute cost estimated small ($5–15/month at XS warehouse, mostly under the 60-second minimum billing floor given this project's low query volume and short build times).
- Reworded the "dbt Projects on Snowflake as orchestration fallback" line in Phase 5 — it's pure bonus-track platform-exploration curiosity now, not framed as contingent on Dagster's success or failure.
- **Decided (design only, not implemented):** the `CI_DEPLOYER` role-scoping follow-up (open since the July 2026 WIF→key-pair session) now has a concrete shape — a two-database, two-role Snowflake dev/prod split: `RAYS_ANALYTICS_DEV` (broad-access `DEV_ROLE`) and `RAYS_ANALYTICS` (scoped `CI_DEPLOYER` role, CI-only). Standard Snowflake/dbt community pattern — separate database per environment plus separate role per environment, not the current schema-only `RAW`/`DEV`/`PROD` split inside one database.
- **Decided:** `dbt build --select state:modified+` becomes the default *local* dev workflow, not just a Phase 8 CI optimization — specifically to control Snowflake credit consumption from frequent local iteration now that DuckDB isn't free local compute for dbt builds anymore.
- **Evaluated and rejected: Delta Lake** as an alternative to dedup-via-dbt-intermediate-model for a future bronze layer. Added complexity (`delta-rs` dependency, Snowflake reading Delta via Delta Direct or Iceberg-wrapping) isn't offset by removing a well-understood, testable dbt dedup step, and it's Databricks-flavored — lower job-market signal for this project's target roles than the Iceberg bonus track already planned, which covers the same "open table format with merge" learning goal.
- **Statcast/pybaseball removed as the assumed next Phase 4 data addition.** Not categorically more useful for this project than other sources worth exploring; no replacement chosen yet — left genuinely open rather than defaulting back to Statcast by habit.

**Orchestration hosting decisions (supersedes the Mac Mini/`launchd` plan from the July 2026 Dagster session):**
- **Mac Mini self-hosting ruled out.** Keeping the Mac Mini continuously powered on for the Dagster daemon doesn't work in practice — tested, not theoretical — and remote access to it when not physically at hand is a significant practical pain, defeating the point of always-on orchestration. Same plainly-stated-reversal voice as the WIF→key-pair and GitHub-Actions-cron-as-long-term-scheduler reversals elsewhere in this project.
- **Dagster Cloud (Solo/Starter) re-confirmed disqualifying, this time with the actual math**, not just general pricing-change awareness: Solo is $10/month base plus $0.04/credit, 1 credit = 1 asset materialization or op execution. `dagster-dbt` generates one asset *per dbt model*, not per project — at this project's ~48 dbt models plus dlt source assets, that's ~49 assets. A comparable published example (50 dbt models, materialized daily) runs ~1,500 credits/month, ~$60/month in credits alone before the base fee — nearly the entire project's monthly budget on orchestration alone. Also rejected: Dagster+ Serverless (adds $0.010/min compute on top of credits) and Dagster+ Hybrid with a local agent (fits the old no-Docker-on-Mac-Mini constraint but doesn't fix the cost problem — credit billing is driven by asset count, not by which agent runs the code).
- **GitHub Actions cron ruled out as a long-term orchestrator**, separate from its already-documented reliability issues (scheduler delays since Feb 2026, 60-day-inactivity auto-disable): it doesn't teach the actual orchestration principles this phase exists to build — asset graph, lineage, dbt-model-level asset checks.
- **"Docker is intentionally avoided" reversed.** Original reasoning was the Mac Mini's 16GB RAM ceiling. Docker now runs on a separate VPS, not the Mac Mini, so that constraint doesn't apply to it anymore. Updated everywhere this assumption appeared: Key Environment Decisions, the "Why 16GB Mac Mini is sufficient" note, and the Tools Not in the Stack table (Docker row removed, replaced with a note explaining the reversal).
- **AWS-native deployment (EC2/ECS/RDS/S3 IO manager) evaluated and rejected.** EC2-hosted Docker Compose is architecturally identical to the VPS plan but costs more; ECS adds AWS-specific complexity (task definitions, IAM roles, VPC/subnet config, Fargate/EC2 launch types) built for concurrent-scaling workloads this solo, ~daily pipeline doesn't have; RDS was considered for automated Postgres backups but rejected in favor of the VPS provider's built-in backup feature (simpler, cheaper, no second cloud vendor relationship); S3 as a Dagster I/O manager is a different feature (passing data between ops during parallel execution) that doesn't apply to this pipeline's shape.
- **Decided: self-hosted Dagster OSS on a small VPS via Docker Compose.** Architecture: four services, not three — `dagster-webserver`, `dagster-daemon`, a dedicated user-code gRPC server (separate from webserver/daemon), and Postgres for run/event storage.
  - **Postgres, not S3 or Snowflake, for run/event storage:** Dagster's storage layer only implements a real run/event backend for SQLite/Postgres/MySQL — no S3 or Snowflake backend exists. Snowflake specifically would also be economically wrong for this workload even if it existed — run/event writes are frequent small transactions (every materialization, every sensor tick), the opposite shape from Snowflake's batch-scan/warehouse-second billing model, recreating the same credit-cost problem that ruled out Dagster Cloud, self-inflicted via the Snowflake bill instead.
  - **Postgres over SQLite-on-a-volume:** Dagster's own docs recommend Postgres for production given SQLite's single-writer limitation, and three processes (webserver, daemon, user-code server) will be hitting this store concurrently.
  - **Self-hosted Postgres over managed free tiers (Neon, Supabase):** Neon's scale-to-zero value doesn't apply since the daemon polls continuously and never idles — its ~100 CU-hours/month free tier would be exhausted in days. Supabase's free tier caps at 500MB and pauses inactive projects. Both also reintroduce the external-vendor-free-tier risk already rejected twice (Dagster Cloud, Prefect Cloud Hobby).
  - **Tailscale as a Docker Compose sidecar** (`network_mode: service:tailscale`) attached to the webserver — the webserver container never binds a public port, reachable only via the tailnet. A sidecar, not a bolt-on VPN layer.
  - **Run/event history durability, decided:** accept provider-level automated backups (e.g. ~20% of instance cost on Hetzner, full-disk snapshot) as sufficient, or accept losing run history entirely on VPS failure as a real but low-stakes outcome — low-stakes because actual pipeline data lives in Snowflake, dlt state lives in destination-system tables, and all code/config lives in Git; only the orchestration run/event timeline is VPS-local, and losing it just means an empty history that repopulates from the next successful run. A custom `pg_dump`/WAL-G backup pipeline was researched and explicitly **not** chosen.
  - **Optional, not required:** `S3ComputeLogManager` to stream compute logs to S3, reusing Iceberg-bonus-track credentials — a nice-to-have, not a Phase 5 dependency.
  - **VPS provider not decided.** Hetzner discussed favorably on cost; no provider, region, or instance size committed — open for next session.
- Removed all `launchd` LaunchAgent language from CLAUDE.md (Mac-reboot-survival specific, no longer applicable) and reframed the "extended Mac downtime" failure-mode discussion as "VPS downtime."

**Documentation-only session — no code, Dockerfiles, `profiles.yml`/`ci.yml`/Makefile changes, or VPS provisioning.** Where a decision implies future setup work, it's captured as "decided, not yet implemented," matching the existing `CI_DEPLOYER` tracking pattern.

**Resolved later this session — CI's response to dropping DuckDB as a build target (decided, not yet implemented):**
- **PR-time job:** changes from a DuckDB build to a Snowflake dev-target build — `dbt build --select state:modified+` against `RAYS_ANALYTICS_DEV` under `DEV_ROLE` (the two-database split decided above). This makes every PR spend real, small Snowflake credits where it previously cost nothing; `state:modified+` exists specifically to bound that cost to changed models and their dependents, not to eliminate it.
- **Merge-to-main job:** unchanged in shape — full `dbt build` against `RAYS_ANALYTICS` (prod) under the scoped `CI_DEPLOYER` role.
- **`profiles.yml`'s `dev_duck` target is removed, not kept as a fallback.** Reviving it for CI would reintroduce the dialect-portability/split-brain problem dropping DuckDB as a build target was meant to solve — deliberately documented so it doesn't get quietly re-added later.
- **`make dbt-build-duckdb` is removed** as a dbt-build Makefile target. A simple "open the DuckDB CLI for scratchpad queries" target is a separate, much simpler target with no dbt invocation — noted as optional, not assumed wanted.
- Still documentation-only: no actual `ci.yml`/`profiles.yml`/Makefile edits this session, matching the "decided, not yet implemented" pattern used elsewhere in this doc.

**Active branch:** `docs/architecture-session-vps-orchestration-duckdb-dropped` — docs-only, no code changes, same pattern as prior `docs/update-claude-md-phase*` branches.

**Next actions:**
1. Implement the resolved CI design above: update `ci.yml`, `profiles.yml` (remove `dev_duck`), and the `Makefile` (remove `dbt-build-duckdb`)
2. Decide VPS provider/region/instance size (Hetzner leading candidate, not committed)
3. Stand up the four-service Docker Compose stack + Tailscale sidecar on the chosen VPS
4. Wrap the `games` dlt pipeline as a Dagster asset; generate dbt model assets via `@dbt_assets` off `manifest.json`
5. Add Dagster asset checks for freshness (from dbt `meta` config) and email alerting
6. Decide the next data source to add (Statcast/pybaseball no longer assumed by default)
7. Implement the `CI_DEPLOYER` / two-database split design decided this session
8. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence

---

### 2026-08-30 — Phase 5: Dagster/VPS orchestration abandoned, decommissioned from main

**Summary: the self-hosted Dagster OSS on a DigitalOcean VPS build (started July 2026) is abandoned.** Root cause: the MLB Stats API blocks DigitalOcean's IP range at the CDN level. This isn't a code bug or a config issue in this project — it's a network-level block on the hosting provider's IP space, confirmed by isolating the variable via multi-environment testing (same pipeline code, same request, different source IP/network — requests failed only from the DigitalOcean-hosted environment, succeeded from others). No known workaround fits this project's scope (no proxy/relay layer being added just to keep a VPS alive), so the VPS approach is a dead end for this specific data source regardless of which orchestrator runs on it.

**What was actually built before the block was found, for the record:**
- SSH key pair generated, DigitalOcean droplet provisioned (NYC3, Basic 2vCPU/4GB/80GB, Ubuntu 24.04), hardened (non-root user, root SSH login disabled, password auth disabled, ufw active with SSH-only).
- Docker + Docker Compose installed on the droplet; a four-service stack (`dagster-webserver`, `dagster-daemon`, a dedicated user-code gRPC server, Postgres for run/event storage) plus a Tailscale sidecar (`network_mode: service:tailscale`, webserver never binds a public port) written and successfully deployed — all five containers came up clean, Tailscale sidecar confirmed joined the tailnet.
- **Daemon bug found and fixed:** `docker-compose.yml` initially launched the daemon without the correct workspace flag, so it couldn't locate the user-code gRPC server — fixed by passing the explicit workspace argument the daemon needs to find `workspace.yaml`.
- **Credential/Compose-secrets work:** Postgres credentials wired into the Compose stack via environment variables rather than hardcoded in `docker-compose.yml`, following the project's existing `.env`-based secrets pattern. (Flagged separately in CLAUDE.md: Claude Code reading `.env` directly while doing this wiring work was noted as a leak-surface risk to watch going forward.)
- Build-context/path issues in `Dockerfile.user_code` (context is repo root, so `COPY` paths for anything under `orchestration/` needed the `orchestration/` prefix) hit and fixed.

**How the IP-blocking issue was isolated:** ran the same `pipelines/mlb_games.py` pull against the MLB Stats API from multiple environments — local Mac, and the DigitalOcean droplet — with the DigitalOcean-hosted attempt failing where every other environment succeeded, pointing at the droplet's network/IP rather than the code.

**Decision:** abandon Dagster OSS on a self-hosted VPS entirely. Orchestration for production scheduling pivots to GitHub Actions + dbt/dlt native tooling (design not yet implemented — see CLAUDE.md Current Status for next actions). GitHub Actions keeps its existing PR/merge-time gate role in `ci.yml` unchanged either way.

**This session's cleanup (branch `chore/decommission-dagster-vps`):**
- Deleted `orchestration/` entirely (`Dockerfile.dagster`, `Dockerfile.user_code`, `docker-compose.yml`, `dagster.yaml`, `workspace.yaml`, `user_code/`).
- Removed the `dagster`/`dagster-dbt`/`dagster-dlt`/`dagster-postgres` optional-dependencies extra from `pyproject.toml` (the extra is gone entirely, not left empty) and regenerated `uv.lock`.
- Removed the module-level `games_source`/`games_pipeline` objects from `pipelines/mlb_games.py` — these existed solely so `dagster-dlt`'s `@dlt_assets` could import them; the CLI path (`games()`, `mlb_stats_api()`, the `argparse` block) is untouched and remains the way a future GitHub Actions workflow will invoke the pipeline.
- Rewrote CLAUDE.md's Phase 5 section, stack table, cost estimate, and related Key Architectural Decisions bullets to describe the reversal honestly rather than deleting the history.

**Full prior implementation and a complete retrospective are preserved on `archive/phase-5-dagster-vps`** (retrospective doc: `archive/phase-5-dagster-vps-retrospective.md` on that branch) — nothing about the Dagster/VPS work is lost, it's just off `main`.

**Next actions:**
1. Design GitHub Actions-based production scheduling for the `games` dlt pipeline + dbt build (cron trigger, credential handling, run-failure alerting)
2. Design "run succeeded but data is wrong" observability now that Dagster asset checks are off the table (e.g. `dbt source freshness` as a CI step, or Elementary)
3. Decide the next data source to add — Statcast/pybaseball no longer assumed by default
4. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence
