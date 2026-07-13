# Rays Analytics — Project Instructions

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

My name is Dyllyn Giles. I'm based in Lexington, Kentucky. I came in with dbt and BI experience but no hands-on modern cloud warehouse experience — this project is where that's been built from scratch. My goal is to build a complete, portfolio-ready modern ELT stack for learning and career development. My personal knowledge system is a pencil and notebook. I prefer to understand what I'm doing rather than just following commands.

**Why I'm actually doing this project:** curiosity and enjoyment, full stop. Job marketability and patterns transferable to my day job are real and welcome, but they are not the filter for what's worth exploring. Don't gate discussing, exploring, or prototyping an idea behind "does this earn its place" — that scrutiny is for decisions about what becomes permanent, maintained stack infrastructure, not for whether something's worth looking at. Default to following interesting tangents.

That said, I still want honest pushback when something is actually unsound, outdated, or solving a problem that doesn't exist — that's different from ROI-gating, and I want it regardless of how fun the idea sounded going in. Real constraint I do care about: I'm not trying to spend a lot of money. Feel free to flag other practical parameters as they come up — ongoing maintenance burden (separate from whether something's resume-worthy), new credentials meaning new security surface area, and the 16GB RAM ceiling on my machine are the ones that have come up so far.

I'm also deliberately going deep on platform-specific exploration (Query Profile, role hierarchy, catalog mechanics) on its own terms, not just when strictly needed for the build. Same applies to DuckDB once Phase 4 work resumes.

---

### My Machine

- M4 Mac Mini, 16GB RAM
- macOS, Apple Silicon (aarch64)

---

### Local Environment

- Homebrew (package manager)
- UV 0.11.17 (Python package and environment manager — replaces both pip and pyenv)
- Python 3.12.13 managed by UV
- VS Code with extensions: dbt Power User, Python, GitLens, Claude Code
- GitHub account connected via SSH key (Ed25519)
- tealdeer installed for command reference (`tldr <command>`)
- DBeaver installed but not actually used — adds friction for no benefit at this project's scale; DuckDB CLI is the preferred path for ad hoc local queries
- DuckDB CLI installed via `brew install duckdb` — invoke as `duckdb <path>`. **Always use the absolute path** (`/Users/dyllyngiles/projects/rays-analytics/dev.duckdb`) — a relative path opens or silently creates a different, empty file depending on current working directory. This same class of bug has now bitten in three different tools (`dbt build` without `DUCKDB_PATH` set, the dlt pipeline before it was parameterized, and the CLI itself) — see Project Structure section for the general pattern.

---

### Key Environment Decisions

**UV replaces both pip and pyenv.** No shims, no PATH conflicts, 10–100x faster than pip. `uv add <package>` updates both `pyproject.toml` and `uv.lock` together. Confirmed as the 2026 community standard for analytics engineering.

**Python 3.12.13** was chosen for dbt-snowflake adapter compatibility.

**The virtual environment lives at repo root** — `~/projects/rays-analytics/.venv` — not inside the `rays_analytics/` dbt subfolder. This keeps a single venv accessible to both the loader script and dbt commands without path gymnastics.

**Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`**, both at repo root.
- Install locally: `uv sync`
- Install in CI: `uv sync --locked`

`--locked` and `--frozen` are not the same thing:
- `--locked`: Resolves dependencies, then **fails if the result would differ from the committed `uv.lock`**. Catches drift between `pyproject.toml` and the lockfile. This is the correct CI choice.
- `--frozen`: Skips resolution entirely and installs whatever is in `uv.lock` without checking whether it matches `pyproject.toml`. Useful in deployment contexts where you want speed and have already verified consistency upstream. Does not catch lockfile drift.

**Docker is intentionally avoided.** 16GB RAM constraint, and the entire stack runs as Python or Node processes.

**`profiles.yml` lives at `~/.dbt/profiles.yml`** — never committed to the repo. Local config points to Snowflake DEV schema. DuckDB target retained as `dev_duck` for reference.

**DuckDB path is always a relative path** (`dev.duckdb`) from repo root, never hardcoded absolute. The `DUCKDB_PATH` environment variable overrides it in CI.

**UV does not load `.env` files automatically.** Use `uv run --env-file .env <command>` to load them explicitly — this works for any command run inside the venv, not just Python scripts (e.g. `uv run --env-file .env dbt build`, `uv run --env-file .env python mlb_pipeline.py`). For scripts that need environment variables at import time (dlt pipelines, Claude API calls), use python-dotenv: `uv add python-dotenv`, then `from dotenv import load_dotenv; load_dotenv()` at the top of the script.

---

### The Stack

| Layer | Tool | Notes |
|---|---|---|
| Ingestion | dlt | Python library, no Docker |
| Bronze storage | Amazon S3 | Same region as Snowflake (us-east-2); raw Iceberg tables, engine-agnostic |
| Iceberg catalog | Snowflake Open Catalog (managed Apache Polaris) | Free during current billing period; resolves CI reachability; same software as self-hosted Polaris if revisited later |
| Warehouse (local dev) | DuckDB | Gitignored, single-file |
| Warehouse (cloud) | Snowflake | ~$30–40/month, X-Small, 60-sec auto-suspend |
| Transformation | dbt Core + dbt-snowflake | |
| Semantic layer | MetricFlow + Cube Core/Cloud free | |
| Orchestration | Dagster OSS or Prefect Cloud free | |
| Observability | Elementary | dbt package |
| BI | Evidence | Code-first, Git-native |
| Version control + CI | GitHub + GitHub Actions | |
| Notebooks | Marimo | Added in Phase 4 |
| AI development | Claude Pro + Claude Code + Anthropic API | Phase 7+ |

### Scope Tracks (added June 2026)

Roadmap is split into two tracks so the application timeline isn't gated by platform-depth exploration that's fun but not required.

**Core path (apply-ready, collapsed timeline):**
- Phase 4, slimmed: dlt → Snowflake `RAW` directly. No bronze/Iceberg layer in this pass — closes the manual-CSV-stopgap gap without the storage-layer detour.
- Phase 5, slimmed: GitHub Actions with an explicit scheduled dependency between loader and `dbt build`. No orchestrator bake-off required for core.
- Phase 6, elevated: MetricFlow + Snowflake Semantic Views are core deliverables, not optional — this is the project's strongest differentiator for analytics-engineering-style work. Cube's necessity is being reconsidered (see Key Architectural Decisions).
- Phase 8, pulled forward: README + walkthrough — cheap, high-leverage, doesn't depend on other phases finishing.
- New, low-effort, could land early: a public self-serve demo — Evidence's Universal SQL (DuckDB-WASM) running live SQL in the visitor's browser against exported Parquet snapshots of the mart/metrics layer, deployed as a static GitHub Pages site. Zero backend, zero cost, zero credentials exposed.

**Bonus / platform-depth track (curiosity-driven, no deadline, doesn't block applying):**
- Bronze layer: S3 + Iceberg + Snowflake Open Catalog, with a future self-hosted Polaris or Lakekeeper experiment
- Orchestration bake-off: Dagster OSS vs. Prefect vs. dbt Projects on Snowflake (Airflow exposure optional — common in AE postings but not required; concepts transfer)
- Deep Snowflake platform exploration: Time Travel, Zero-Copy Cloning, Cortex, Marketplace, Streamlit in Snowflake
- Phase 7 AI/MCP layer, including a MotherDuck Dives sandbox experiment (needs a throwaway data copy living in MotherDuck — not a stack decision)
- Self-serve BI tool decision: Lightdash (dbt-native metrics layer, genuine point-and-click self-serve — but self-hosting needs Docker, which conflicts with the no-Docker stance and needs a deliberate call) vs. Metabase (no Docker, but metrics get redefined in Metabase itself instead of inheriting from dbt)

---

**Snowflake-native additions (Phase 3+):**
- dbt Projects on Snowflake (GA November 2025) — run dbt Core natively inside Snowflake, via a Git-connected Workspace + a deployed `DBT PROJECT` object. Explored in Phase 3 (currently unconfigured — requires a GitHub API integration and a Git-connected Workspace to populate). Deferred — will be weighed against Dagster OSS/Prefect/GitHub Actions when finalizing the Phase 5 orchestration choice.
- Snowflake Semantic Views (Standard SQL querying GA March 2026) — warehouse-native semantic layer, zero extra cost
- Snowflake Cortex Analyst — NL querying over semantic views, ~$5–15/month at hobby scale

**Estimated monthly cost: ~$60–75/month.** Snowflake ~$30–40; Cortex experiments ~$5–15; Claude Pro $20; Anthropic API (Phase 7+) ~$5–10; everything else free.

---

### Key Architectural Decisions

**Why dlt over Airbyte:** Airbyte is Docker-heavy, its free tier has been uncertain, and dlt teaches ingestion at code level rather than abstracting it behind a UI. Engineering-driven teams increasingly use dlt as their first choice.

**Why dlt over Snowflake Openflow (resolved June 2026):** Openflow is the right tool when a source is one of its ~20 supported connectors and no customization is needed. MLB Stats API and pybaseball/Statcast are bespoke sources outside that list — exactly dlt's home turf. Openflow also requires standing up real infrastructure (BYOC in a VPC, or Snowpark Container Services) for a single custom source, which cuts against both the RAM ceiling and the open-source-portability thesis, since Openflow's orchestration layer is Snowflake-proprietary even though NiFi underneath is open. dlt remains the right call, full stop — no longer an open question gating Phase 4.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow YAML is the OSI v1.0 reference implementation — learning it now means learning the emerging industry standard for semantic layers. Cube provides the API exposure layer that dbt Cloud would otherwise lock behind $100/month. The combination covers the full workflow at zero cost.

**Cube's necessity reconsidered (added June 2026):** Cube's job is exposing governed metrics over an API for other tools to consume — it isn't itself a place where someone self-serves a dashboard. The better target experience is "anyone can click around and build their own view," which Cube doesn't provide on its own. MetricFlow + Snowflake Semantic Views stay core regardless; Cube is now optional pending the Phase 6 BI-tool decision (Lightdash/Metabase/Evidence, see Scope Tracks above).

**Why Dagster OSS or Prefect over Dagster Cloud:** Dagster Cloud removed free credits from Solo and Starter plans May 1, 2026 — every asset materialization is now billed from zero at ~$0.035–0.040/credit with no grandfathering. Dagster OSS running locally as a Python process, or Prefect Cloud free Hobby tier (2 users, 5 workflows, 500 minutes serverless compute, no credit card required), covers the same learning goals.

**Why S3 + Iceberg + Snowflake Open Catalog over self-hosted Polaris or AWS Glue (decided June 2026; rescoped to bonus track):** Adding a bronze layer — raw data landing in S3 as Iceberg tables instead of being loaded directly into Snowflake — decouples storage from compute. Snowflake and DuckDB can both read the exact same physical files without separate load steps, extending the dbt-portability thesis (swap transformation engines, same SQL) to the storage layer (swap query engines, same data). Three catalog options were weighed:
- **Self-hosted Apache Polaris** — full control, fully open-source, but introduces a server only reachable from the Mac Mini. This breaks CI: GitHub Actions runners can't reach a catalog running on a laptop.
- **AWS Glue** — zero-ops, matches the AWS dependency already accepted via S3, and the market-leading catalog by adoption. But it's proprietary, and doesn't extend the open-source-first preference (dbt Core, Iceberg, OSI) the way Polaris does.
- **Snowflake Open Catalog** — won. It's a managed hosting of the *actual* open-source Apache Polaris (same software, same principal/role model), free during the current billing period (0.5 credits/million requests after — negligible at hobby scale), and reachable by both local dev and CI since it's not self-hosted.

Self-hosted Polaris isn't rejected, just deferred — since Open Catalog runs the identical software, switching to self-hosting later (for the hands-on "I ran this myself" experience) costs little beyond re-registering a handful of tables and re-pointing engine configs. Whichever catalog is active, only one should ever write to a given S3 location — never register the same Iceberg table in two catalogs simultaneously. **This entire decision now lives in the bonus track (see Scope Tracks above) — core Phase 4 writes dlt straight into Snowflake `RAW`, no bronze layer, to keep the application timeline unblocked.** The architecture and reasoning stand for whenever the bonus-track work resumes.

**Why Evidence over Metabase:** Code-first, Git-native, designed for analytics engineers. Fits the everything-as-code philosophy of the stack. Cube Cloud free tier is dev/test only — if it changes, Cube Core runs as a local Node process at zero cost: `npm install -g @cubejs-backend/cli`.

**Public self-serve demo, added June 2026:** Evidence ships a DuckDB engine to the browser via WebAssembly (Universal SQL) — filters and dropdowns run live SQL client-side against Parquet snapshots, with no server round-trip. That means a static GitHub Pages site, built from exported mart/metrics Parquet files, can let any visitor interact with the data live in their own browser — no backend, no credentials exposed, no per-visitor cost. This is a separate use case from the Lightdash/Metabase self-serve BI decision below: it's for a public, zero-infra, anyone-with-a-browser experience, not an internal team tool. Perspective (FINOS) is the candidate if literal drag-and-drop pivoting matters more than Evidence's filter-driven interactivity — decision deferred until this gets built.

**Self-serve BI tool decision, added June 2026, deferred to Phase 6:** Lightdash reads metrics/dimensions directly from dbt YAML and gives a genuine point-and-click explorer for non-technical users — closer to the "anyone can build their own dashboard" goal than Cube+Evidence ever was. The catch: standard self-hosting runs on Docker (Node + Postgres), which conflicts with the no-Docker stance — worth a deliberate call (reconsider Docker for this one component vs. Lightdash Cloud's trial vs. Metabase as the no-Docker alternative, which trades away dbt-native metric governance). Not yet decided.

**dlt resource design for `games` — completed games only, no live/in-progress state (decided June 2026):** The MLB Stats API schedule endpoint returns every game for a season regardless of status — `Scheduled`, `In Progress`, `Final`, etc. The `games` resource filters to `Final`/`Completed Early` only before yielding, so unplayed or in-progress games never reach `raw.games`. This was a deliberate scope call, not a technical limitation: landing live game state would require loosening `not_null` tests on score columns, expanding `accepted_values` on `game_status`, and rethinking how `rays_win` behaves for a game with no result yet. None of that was judged worth it for the core path — the resource always re-pulls the full current season on every run, so a game picked up as `Final` for the first time merges in cleanly the moment it's actually decided, with no half-loaded intermediate state ever touching the table.

**Why `games` doesn't use dlt's `incremental()` cursor (decided June 2026):** dlt's `dlt.sources.incremental()` helper is built for cursor-based filtering — "give me rows where `updated_at` > last-seen-value." The schedule endpoint doesn't have that shape: a 2022 game's result doesn't change, but the endpoint also doesn't expose a true modified-since cursor, and it returns the whole season every call regardless. The actual pattern used instead is full-season re-pull + `merge` write-disposition keyed on `game_pk` — correct for this data's small size and shape, not a missing feature. **This will not hold at Statcast scale** — see Phase 4 notes; pitch-level data has real cursor potential (game date) and re-pulling full history every run isn't viable at that volume.

**dlt pipeline destination is parameterized, not hardcoded (decided June 2026):** `mlb_pipeline.py` takes `--destination duckdb|snowflake` as a CLI flag (default `duckdb`). The resource/source code is destination-agnostic by construction — only the `pipeline.run()` call's destination argument changes. This was chosen specifically so DuckDB can be refreshed freely and at zero cost (real, current data — not a stale fixture) while Snowflake compute is only spent when explicitly requested. CI's future DuckDB job and Snowflake job will call the same script with different flags, not different scripts.

**dlt table ownership gotcha (hit and resolved June 2026):** dlt cannot retrofit its internal tracking columns (`_dlt_id`, `_dlt_load_id`) onto a table it didn't create — attempting to `ALTER TABLE ADD COLUMN ... NOT NULL/UNIQUE` on a pre-existing table fails (DuckDB: `Parser Error: Adding columns with constraints not yet supported`). Hit when `dev.duckdb`'s `raw.games` still held data from the old manual `load_mlb_data.py` script. Fix: any table dlt is meant to own must be created by dlt from a clean slate — drop the table (or the whole local file) and let the pipeline recreate it. **This is a known, not-yet-resolved blocker for the first `--destination snowflake` run** — `RAYS_ANALYTICS.RAW.GAMES` still holds the Phase 3 manual-CSV-stopgap data and will hit the identical error.

**`dim_teams`/`dim_venues` deduplication — most-recent-name-wins (decided June 2026):** Both models originally deduped on `(id, name)` as a pair via `union`/`select distinct`. This broke the moment 2025–2026 data entered the table — team and venue names can change over time for the same numeric id (e.g. a team dropping a city name ahead of relocation; ballpark sponsorship renames), producing two rows for one id and failing the `unique` test on `team_id`/`venue_id`. Fixed by ranking rows per id by `game_date desc` (`row_number()` window function) and keeping only the most recent name. Chosen deliberately over two alternatives: always-earliest-name (rejected — shows stale branding) and full slowly-changing-dimension history (rejected for now — more correct but more work than the core path needs; revisit if a future phase actually needs "what was this called in 2022" as a queryable fact).

**Secrets consolidation — single `.env` shared by dbt and dlt, no `.dlt/secrets.toml` (decided July 2026):** The first real `--destination snowflake` run exposed a gap: dlt keeps its own credential store, entirely separate from dbt's `~/.dbt/profiles.yml`, even though both point at the exact same Snowflake account and service user. The naive fix was a `.dlt/secrets.toml` — a second, tool-specific secrets file duplicating values (account identifier, service user, key path, warehouse, role, database) already sitting in `profiles.yml`. Instead, both tools now read from one gitignored `.env` at repo root: dlt via its native `DESTINATION__SNOWFLAKE__CREDENTIALS__*` environment variable convention, and `profiles.yml` via dbt's `env_var()` Jinja function pointed at those exact same variable names (see Current `profiles.yml` structure below). One canonical value per secret, referenced from two places instead of duplicated in two files. GitHub Secrets for CI remain a separate, unavoidable third location — a CI runner can't read a local, gitignored `.env` — so this consolidation is scoped to local dev only and doesn't change the Phase 4 CI blocker. Invocation pattern: `uv run --env-file .env <command>`, which loads the file identically for Python scripts and dbt commands.

**Why 16GB Mac Mini is sufficient:** Docker has been removed from the stack entirely. All tools run as Python or Node processes. No containers.

**dbt Core vs dbt Fusion vs dbt Core v2.0:** This space moved significantly at Snowflake Summit in June 2026. dbt Labs open-sourced the Fusion runtime as dbt Core v2.0 under Apache 2.0 — the previous ELv2 license concern no longer applies to the core runtime. However, v2.0 is currently in alpha and dbt Core v1.11.x remains the right choice for this stack. The Fusion distribution (`pip install dbt`) extends the open runtime with proprietary capabilities and is what dbt Labs recommends for most users long-term. The two-engine era is ending — Core and Fusion now share a foundation. Worth monitoring; revisit at Phase 8.

**Snowflake-native dbt:** GA November 2025. No additional licensing cost — pay only warehouse credits. Worth exploring alongside the local dbt workflow in Phase 3.

**Snowflake Semantic Views:** Standard SQL querying GA March 2026. Zero extra cost, zero infrastructure overhead. Snowflake-only, but this stack is Snowflake-only in production.

**dbt/Fivetran merger:** Completed June 1, 2026. George Fraser (Fivetran) is CEO, Tristan Handy (dbt Labs) is President. dbt Core remains Apache 2.0 open source. No impact on this stack. Community sentiment is mixed — the Apache 2.0 floor protects against worst-case scenarios, but long-term investment balance between Core and the commercial platform bears watching.

---

### Tools Not in the Stack

| Tool | Reason excluded |
|---|---|
| Airbyte | Docker-heavy; free tier uncertain; dlt teaches more |
| Dagster Cloud | Free credits removed May 2026; per-asset billing from zero |
| dbt Cloud | $100/seat/month for Semantic Layer API access |
| dbt Fusion (distribution) | Proprietary extensions above the Apache 2.0 runtime; v2.0 alpha not production-ready; Core v1.11.x is current and stable |
| Fivetran | Pricing restructured March 2025; per-connector costs increased 50–60% |
| Jupyter | Replaced by Marimo — git-friendly, no hidden state, saves as Python files |
| Docker | RAM constraint; not needed for this stack |
| MotherDuck | Considered as a third portability target (alongside DuckDB/Snowflake) in June 2026; deprioritized — the interest is real but work-related, not specific to this project. DuckDB remains the local dev engine, Snowflake the named production target. |
| AWS Glue | Considered for the Iceberg catalog; zero-ops and matches the existing AWS dependency via S3, but proprietary — doesn't extend the open-source-first preference the way Polaris/Open Catalog does. Revisit only if Open Catalog's cost or limits become a real problem. |
| Airflow | Shows up frequently in AE job postings, but not required — asset-based orchestration concepts (DAGs, dependencies, retries, scheduling) transfer from Dagster/Prefect. Not worth standing up just for resume-keyword matching; added June 2026. |

---

## Part 2 — Current Project State

*This section changes with each phase. Update it as work progresses: file structure as models are added, phase status as tasks complete, known issues as they're fixed or discovered.*

---

### Project Overview

- **GitHub repo:** github.com/dyllyngiles/rays-analytics
- **dbt docs site:** dyllyngiles.github.io/rays-analytics
- **Docs publish script:** `./publish_docs.sh` from project root — run after any model changes, before opening a PR

---

### Snowflake Account

- **Edition:** Standard, AWS us-east-2
- **Account identifier:** stored locally in `~/.dbt/profiles.yml` — not documented here
- **Warehouse:** COMPUTE_WH (X-Small, 60-sec auto-suspend, auto-resume on)
- **Resource monitor:** MONTHLY_SPEND_CAP — 15 credits/month, notify at 75%, suspend at 100%
- **Database:** RAYS_ANALYTICS
- **Schemas:** RAW, DEV, PROD
- **Service user:** DBT_SERVICE_USER — TYPE = SERVICE, SYSADMIN role, key-pair auth
- **Key location:** `~/.ssh/dbt_service_user_rsa_key_p8.pem` (PKCS#8 format)

---

### Snowflake Key-Pair Auth Notes

Key-pair auth requires PKCS#8 format — the standard `openssl genrsa` output is PKCS#1 and will fail with a JWT error. Generate keys with:

```bash
openssl genrsa -out dbt_service_user_rsa_key.pem 2048
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt \
  -in dbt_service_user_rsa_key.pem \
  -out dbt_service_user_rsa_key_p8.pem
openssl rsa -in dbt_service_user_rsa_key.pem -pubout \
  -out dbt_service_user_rsa_key.pub
```

Register the public key in Snowflake (base64 block only, no header/footer):

```bash
grep -v "BEGIN\|END" ~/.ssh/dbt_service_user_rsa_key.pub | tr -d '\n'
```

```sql
ALTER USER DBT_SERVICE_USER SET RSA_PUBLIC_KEY='<paste_base64_here>';
```

**Account identifier gotcha:** The identifier shown in the browser URL is not what dbt needs. Use `SELECT SYSTEM$ALLOWLIST()` and look for the `SNOWFLAKE_DEPLOYMENT` entry to find the correct regional format. The regionless format (`org-account`) did not work; the regional format (`locator.region.aws`) did.

---

### Snowflake Role Hierarchy & Privilege Notes

**Hierarchy (within a single account):**
```
ACCOUNTADMIN
  ├── SECURITYADMIN
  │      └── USERADMIN
  └── SYSADMIN
         └── (custom roles get granted here)

PUBLIC — implicit floor every role gets
```
`ACCOUNTADMIN` inherits `SYSADMIN` and `SECURITYADMIN`'s privileges — not the other way around. `ORGADMIN` is a separate, org-level role for managing multiple Snowflake accounts; mostly irrelevant for this single-account project, with one exception: **`ORGADMIN` is required to create a Snowflake Open Catalog account** (see Bronze Layer & Iceberg Catalog notes below).

**Default role decision:** `SYSADMIN` is the default Snowsight role going forward, not `ACCOUNTADMIN`. Set via:
```sql
ALTER USER <username> SET DEFAULT_ROLE = SYSADMIN;
```
`ACCOUNTADMIN` is reserved for genuinely account-level tasks only: resource monitors, billing, and rare service-account/user management. Full four-role rotation (`ACCOUNTADMIN`/`SECURITYADMIN`/`USERADMIN`/`SYSADMIN`) is enterprise ceremony that isn't worth it for a one-person project — two roles is the right-sized version here.

**The gotcha (bit three times now — twice in Phase 3, once in Phase 4):** anything created through the Snowsight UI under your personal session is owned by whatever role that session defaults to. If that's `ACCOUNTADMIN` and `DBT_SERVICE_USER` runs as `SYSADMIN`, `SYSADMIN` has zero automatic access — Snowflake's role hierarchy doesn't flow downward to it. This surfaced as three different error messages for three different object types:
- **Table** (`RAW.GAMES`, loaded via the Catalog UI): `SQL compilation error: Object ... does not exist or not authorized` — Snowflake intentionally won't confirm whether an unauthorized role's target even exists.
- **Warehouse** (`COMPUTE_WH`, owned by `ACCOUNTADMIN`): `No active warehouse selected in the current session` — the dbt-snowflake connector passes `warehouse:` as a connection parameter (an implicit `USE WAREHOUSE`); if the role lacks `USAGE` on it, the connector fails to set it *silently* rather than erroring at connect time. The error only surfaces later, when a query actually needs compute (which is also why a view model succeeded — `CREATE VIEW` is metadata-only — while table models failed immediately after).
- **Schema** (`RAW`, hit in Phase 4 when dlt tried to recreate `GAMES` from scratch after the old table was dropped): `SQL access control error: Insufficient privileges to operate on schema 'RAW'. Your primary role SYSADMIN must have CREATE TABLE granted on SCHEMA RAYS_ANALYTICS.RAW.` A table-level `SELECT` grant doesn't imply schema-level `CREATE TABLE` — reading an existing table and originating a new one in that schema are separate privileges. This one only surfaced once the old `ACCOUNTADMIN`-owned table was gone, since nothing had ever needed to *create* a table in `RAW` before.

**Fix, either case:** grant the missing privilege explicitly, run as the object's owning role:
```sql
GRANT SELECT ON TABLE RAYS_ANALYTICS.RAW.GAMES TO ROLE SYSADMIN;
GRANT USAGE, OPERATE ON WAREHOUSE COMPUTE_WH TO ROLE SYSADMIN;
GRANT CREATE TABLE ON SCHEMA RAYS_ANALYTICS.RAW TO ROLE SYSADMIN;
```
Better long-term fix: switch the Snowsight role selector to `SYSADMIN` *before* doing any manual UI work (loading data, creating warehouses), so objects are owned by the right role from creation instead of needing retroactive grants. One upside of the schema-level grant specifically: `SYSADMIN` now owns whatever it creates in `RAW` going forward, so future table recreations in that schema are correctly owned from the moment of creation — no more retroactive grants needed there.

---

### Bronze Layer & Iceberg Catalog Notes

**Architecture:** raw data lands in S3 (us-east-2, same region as Snowflake) as Iceberg tables, cataloged through Snowflake Open Catalog. Snowflake and DuckDB both read from this same physical location as separate engines — the catalog resolves "what does this table currently look like" for whichever engine asks. See Key Architectural Decisions in Part 1 for the full reasoning on why Open Catalog won over self-hosted Polaris and AWS Glue.

**Setup requirements:**
- `ORGADMIN` role to create the Open Catalog account itself (one-time, org-level action — the one real exception to "ORGADMIN is irrelevant here")
- An S3 bucket in us-east-2, with IAM credentials scoped to it
- A storage configuration in Open Catalog pointing at that bucket

**Cost:** free during the current billing period; 0.5 credits/million requests once billing starts (~$1/million requests at Standard edition rates) — negligible at this project's query volume.

**Single-writer rule:** only one catalog should ever write to a given S3 Iceberg location. Registering the same table in two catalogs (e.g., both Open Catalog and a self-hosted Polaris instance) risks both silently corrupting each other's metadata pointers, since they don't share transaction state.

**Switching catalogs later, if ever needed:** because Iceberg tables are self-describing (metadata files already sit in S3 next to the data), switching catalogs is a re-registration + re-pointing operation, not a data migration — the files never move. At this project's table count (low single digits to maybe a dozen post-Statcast), that's an afternoon of work, not a project. Switching specifically between Open Catalog and self-hosted Polaris is the cheapest direction, since they're the same software with the same principal/role model — only the AWS Glue direction requires learning a genuinely different auth model (plain IAM instead of principals/catalog-roles).

**Self-hosted Polaris status:** deferred, not rejected. If the hands-on "ran the server myself" experience becomes its own pebble worth chasing later, the switch from Open Catalog is low-friction for the reasons above. Lakekeeper (Rust, single-binary, lighter footprint than Polaris's JVM+Postgres) is worth a look as an alternative self-hosting target if/when that day comes — same open-source values fit, less weight on the Mac Mini.

---

### Snowsight Navigation (as of June 2026)

Snowflake rolled out a navigation reorganization grouping features into new top-level categories: **Projects** (Worksheets/Workspaces, Notebooks, Streamlit, Dashboards), **Ingestion** (Add data, Migrations, Openflow, Copy history), **Transformation** (dbt projects, Tasks, Dynamic tables), **AI & ML** (Cortex, Snowflake ML), **Monitoring** (query history, container services, job history, traces/logs), **Marketplace**, **Catalog** (Database Explorer, internal marketplace, Apps), **Data sharing**, **Governance & security** (users & roles, network policies, tags & policies), **Compute** (warehouses, compute pools), and **Admin** (billing, contacts, partner connect).

Confirmed mappings worth remembering (old → new):
- **Data → Databases** is now **Catalog → Database Explorer**
- **dbt Projects** moved from Monitoring to **Transformation → dbt projects** — it is *not* nested under Workspaces, even though dbt project files are edited inside a Git-connected Workspace
- **Query History** (and thus Query Profile) stayed put: **Monitoring → Query History**
- **SQL editor:** Projects → Workspaces (renamed from Worksheets, April 20, 2026). **Legacy Worksheets removed June 22, 2026.**

**Caveat:** this UI shifts often enough that exact nav paths shouldn't be trusted long-term without a quick re-check — already had to correct the Database Explorer and dbt Projects locations once this session. Treat anything written here as "true as of June 2026," not permanent.

---

### Current `profiles.yml` structure

```yaml
rays_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__HOST') }}"
      user: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__USERNAME') }}"
      private_key_path: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__PRIVATE_KEY_PATH') }}"
      role: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__ROLE') }}"
      database: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE') }}"
      warehouse: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__WAREHOUSE') }}"
      schema: DEV
      threads: 4
    dev_duck:
      type: duckdb
      path: "{{ env_var('DUCKDB_PATH', 'dev.duckdb') }}"
      threads: 4
```

As of July 2026, the Snowflake credential fields are all `env_var()` calls rather than hardcoded values, pulled from a single gitignored `.env` at repo root that dlt also reads natively (see Key Architectural Decisions, "Secrets consolidation"). `schema: DEV` stays hardcoded deliberately — it's dbt-only config, not a credential shared with any other tool, so it never belonged in the consolidation.

---

### Project Structure

```
~/projects/rays-analytics/          ← project root, Python scripts, git repo
  .venv/                            ← virtual environment (repo root, NOT in rays_analytics/)
  pyproject.toml                    ← project dependencies
  uv.lock                           ← pinned transitive dependency versions
  mlb_pipeline.py                   ← dlt pipeline, MLB Stats API → DuckDB/Snowflake (--destination flag)
  dev.duckdb                        ← local DuckDB file (gitignored)
  .env                              ← Snowflake credentials shared by dbt + dlt (gitignored, never committed)
  publish_docs.sh                   ← publishes dbt docs to GitHub Pages
  README.md                         ← project overview and local setup
  CLAUDE.md                         ← Claude Code context
  .github/
    workflows/
      ci.yml                        ← GitHub Actions CI — runs on every PR to main
  .gitignore
  rays_analytics/                   ← dbt project, all dbt commands run from here
    models/
      staging/
        sources.yml
        schema.yml
        stg_games.sql
      marts/
        schema.yml
        dim_teams.sql
        dim_venues.sql
        fct_games.sql
```

---

### Data Model

- **Source:** MLB Stats API (no auth required)
- **Raw table:** `RAYS_ANALYTICS.RAW.GAMES` in Snowflake — populated by the real `mlb_pipeline.py` dlt pipeline (`--destination snowflake`), owned by `SYSADMIN`. The Phase 3 manual-CSV-stopgap table has been fully retired (dropped and recreated by dlt in July 2026).
- **Rays team ID:** 139
- **Seasons loaded:** 2022–2026 (~740 completed games as of the last real Snowflake load — 162 each for 2022–2025, 92 for the still-in-progress 2026 season; this count grows run-over-run as 2026 games finish)
- **Star schema:** stg_games → dim_teams, dim_venues, fct_games
- **48 tests** — not_null, unique, accepted_values, relationships

**Resolved:** the `MissingArgumentsPropertyInGenericTestDeprecation` warning on the `relationships` test in `models/marts/schema.yml` was fixed in PR #14 (nested arguments under an `arguments:` property, matching the existing `accepted_values` pattern).

---

### Workflow Conventions

- Always `cd rays_analytics` for dbt commands
- Activate venv and navigate at session start:
  ```bash
  cd ~/projects/rays-analytics
  source .venv/bin/activate
  cd rays_analytics
  ```
- Feature branch for every change, no direct commits to main
- After `dbt run` — view compiled SQL in `target/compiled/` or use dbt Power User preview panel
- Close DBeaver before running dbt or Python scripts (DuckDB single-connection limitation)
- Run `./publish_docs.sh` after model changes, before opening a PR
- Use `dbt --help` for command reference, not tldr
- Python scripts run from project root `~/projects/rays-analytics/`, not the dbt subfolder
- Never hardcode absolute file paths in Python scripts — use `os.getenv('VAR', 'relative/default')`
- Default Snowsight role is `SYSADMIN`, not `ACCOUNTADMIN` — switch explicitly to `ACCOUNTADMIN` only for resource monitors, billing, or service-account management (see Snowflake Role Hierarchy notes)
- `git config --global fetch.prune true` is set — every `fetch`/`pull` auto-removes local references to branches already deleted on the remote, so merged feature branches don't linger as stale tracking refs
- GitHub has "automatically delete head branches" enabled — merged PR branches disappear from the remote immediately; local branches still need an explicit `git branch -d` after
- Pull past PR descriptions from the CLI with `gh pr list --state all` then `gh pr view <number>` (or `--json body -q .body` for just the description text) — faster than digging through the GitHub UI
- **Repo audited clean (June 2026):** confirmed via `git ls-files` (nothing sensitive currently tracked) and `git log --all --oneline -- profiles.yml '*.pem' '*.key' '*.env'` (empty — none of those filenames have ever touched git history, not even in a deleted commit). Worth re-running both checks periodically rather than assuming `.gitignore` alone proves anything about the past.
- **One-off exports never get committed.** `.gitignore` includes `/games_export.csv` and `/scratch/` specifically for throwaway data dumps (e.g. the Phase 3 CSV stopgap) — delete them when done, or park them in `/scratch/` if you want to keep them around locally. Don't let scratch files ride along in an unrelated commit.

---

### CI Architecture Notes

The GitHub Actions workflow (`.github/workflows/ci.yml`) currently has **one job**, triggered on `pull_request` to `main` only. It runs `dbt build` against DuckDB, first calling `mlb_pipeline.py --destination duckdb` to populate the local database. This job works correctly as of `main` — an earlier version of this doc claimed it still called the deleted `load_mlb_data.py`; that was stale documentation that never got updated after `feature/dlt-games-pipeline` merged, not the actual state of the repo.

**Target architecture (designed, not yet built):** a second job, gated to run only on `push` to `main` (i.e., post-merge, not on every PR), running `dbt build` against real Snowflake using a dynamically-generated `profiles.yml` with the service user's key-pair credentials pulled from GitHub Secrets (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_PRIVATE_KEY`, `SNOWFLAKE_USER`). DuckDB stays on every PR (fast, free, catches structural errors). This bounds Snowflake compute cost to "once per merged PR," not "once per push to an open PR" — a deliberate cost control. SQL dialect differences mean DuckDB passing doesn't guarantee Snowflake passing; that gap is accepted, not solved, by running Snowflake validation once at merge rather than DuckDB-only forever.

Building this requires: (1) adding GitHub repo secrets for the service user's private key and account identifier, (2) a second job definition with a `push`-only trigger condition, (3) a Snowflake-flavored `profiles.yml` generation step parallel to the existing DuckDB one. Not yet started.

**Actions pinning:** All actions are pinned to exact commit hashes, not floating version tags. The March 2025 tj-actions/changed-files compromise — which leaked secrets from thousands of repositories via a hijacked tag — is the canonical reason why. Current pinned hashes:
- `actions/checkout` v6.0.2 → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `astral-sh/setup-uv` v8.1.0 → `08807647e7069bb48b6ef5acd8ec9567f424441b`

**Dependency installation:** `uv sync --locked` — verifies `uv.lock` is consistent with `pyproject.toml` and fails if they've drifted.

**Dependency auditing:** `uv audit` runs as a CI step. Built into uv 0.10.12+, no additional install required.

**`uv audit` can fail a PR for reasons that have nothing to do with that PR.** It audits whatever's currently pinned in `uv.lock`, so a newly-disclosed CVE against an already-resolved transitive dependency can fail CI on a completely unrelated change (hit this on a docs-only PR — `cryptography` and `msgpack` both had patched CVEs). Fix is a narrow lockfile bump, not a full re-resolve:
```bash
uv lock --upgrade-package cryptography --upgrade-package msgpack
uv sync --locked
```
Run from repo root, not the `rays_analytics/` subfolder — `uv.lock` lives at root.

**UV version:** Pinned to `0.11.17` to match local version exactly.

---

### Learning Roadmap

#### Phase 1 — Foundation ✅ COMPLETE

**Skills locked in:** dbt project structure, staging/mart layering, testing discipline, documentation habits, columnar warehouse thinking, star schema dimensional modeling, feature branch git workflow.

---

#### Phase 2 — Version Control ✅ COMPLETE

**Skills locked in:** Git-based workflow, CI pipeline authoring, PR-driven development, branch protection, secrets management discipline, CI debugging from logs, dependency auditing.

---

#### Phase 3 — Real Warehouse ✅ COMPLETE

**Goal:** Swap the dbt adapter from DuckDB to Snowflake, port all models, configure dev/prod environments, and establish cost controls.

**Completed:**
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
- Dual-job CI architecture (DuckDB-every-PR / Snowflake-on-merge) **designed and documented, not yet implemented.** `ci.yml` on `main` currently has a single DuckDB job triggered on `pull_request` only — no Snowflake job, no GitHub Secrets configured yet. This is real, scoped work, not a doc gap — tracked as a Phase 4 wrap-up item below.
- Workload Identity Federation researched and ruled out — unsupported in dbt-snowflake as of June 2026; key-pair auth confirmed correct ✅
- `RAYS_ANALYTICS.RAW.GAMES` populated via one-time manual CSV stopgap (486 games) ✅
- Full `dbt build` passing against real Snowflake data — models and all 44 tests ✅
- Snowflake privilege/RBAC gotcha hit and resolved twice (table + warehouse ownership) — see Role Hierarchy notes ✅
- Query Profile explored on a compiled model ✅
- dbt Projects on Snowflake explored (found unconfigured; deliberately deferred to Phase 5 decision) ✅

**Skills locked in:** Snowflake architecture, cost monitoring, key-pair authentication, account identifier formats, dbt-snowflake adapter setup, dual-environment CI design (DuckDB/Snowflake split), GitHub Secrets-based service auth in CI, Snowflake RBAC hierarchy and privilege troubleshooting, reading a Query Profile (Statistics pane, partition pruning, why a view vs. table model behaves differently), Snowsight navigation literacy, recognizing when a throwaway stopgap is the right scope vs. pulling a future phase forward prematurely.

---

#### Phase 4 — Ingestion (~1 week, slimmed for core path) — IN PROGRESS

**Resolved June 2026:** dlt over Openflow — see Key Architectural Decisions. No longer a blocking pause.

**Core goal:** Replace `load_mlb_data.py` with a proper dlt pipeline writing directly into `RAYS_ANALYTICS.RAW`; add Statcast data via pybaseball; build staging models over dlt raw output; implement incremental loading. **No bronze/Iceberg layer in this pass** — that work is rescoped to the bonus track (see Scope Tracks, Part 1).

**Completed this session:**
- Phase 3 wrap-up debt cleared: confirmed `DEFAULT_ROLE = SYSADMIN` set on service user; flipped local `profiles.yml` target to `dev_duck`; full `dbt build` passing clean against DuckDB ✅
- `dlt==1.28.1` installed via `uv add "dlt[duckdb,snowflake]"` ✅
- Feature branch `feature/dlt-games-pipeline` created; `load_mlb_data.py` removed via `git rm` ✅
- `mlb_pipeline.py` built at repo root — `games` resource (merge write-disposition, `game_pk` primary key), `mlb_stats_api` source, destination-parameterized via `--destination duckdb|snowflake` CLI arg (defaults to `duckdb` — Snowflake compute only spent when explicitly requested) ✅
- End-to-end DuckDB load verified: 729 completed games across 2022–2026 (2026 partial season, correctly growing run-over-run as games finish) ✅
- `accepted_values` tests on `season` updated to include 2025/2026 in both `staging/schema.yml` and `marts/schema.yml` ✅
- `dim_teams.sql` / `dim_venues.sql` fixed — see Key Architectural Decisions below ✅
- Full `dbt build` passing clean against DuckDB with dlt-sourced data — 48/48 ✅

**Completed since (July 2026 session):**
- `feature/dlt-games-pipeline` confirmed merged to `main` — the `ci.yml` fix and the real Snowflake load both landed; see corrections in CI Architecture Notes and Data Model
- Real `--destination snowflake` run succeeded: ~740 completed games loaded into `RAYS_ANALYTICS.RAW.GAMES`, correctly owned by `SYSADMIN`
- Hit and resolved the third RBAC ownership gotcha (schema-level `CREATE TABLE`) — see Role Hierarchy & Privilege Notes
- Secrets consolidated: single `.env` now shared by dbt and dlt for Snowflake credentials, replacing the need for a separate `.dlt/secrets.toml` — see Key Architectural Decisions

**Known open items:**
- CI dual-job architecture (Snowflake-on-merge) not yet built — see CI Architecture Notes. This is the last remaining Phase 4 blocker.
- Statcast/pybaseball resource not yet started

**Key notes:**
- Incremental loading requires a cursor column — understand dlt state management. **Decided this session:** the `games` resource does NOT use `dlt.sources.incremental()` — see Key Architectural Decisions, "Why games doesn't use dlt's incremental cursor." Statcast will need the real cursor pattern; `games` doesn't fit it.
- Deliberately introduce a schema change and observe how dlt and dbt source freshness tests respond — not yet done

**Bonus-track note (when revisited):** S3 + Iceberg + Snowflake Open Catalog bronze layer — dlt writes once to S3 as Iceberg tables, Snowflake and DuckDB both read from that bronze location as separate engines. One-time setup: an `ORGADMIN`-created Open Catalog account, an S3 bucket in us-east-2, IAM credentials scoped to that bucket. Single-writer discipline: only Open Catalog should ever write to the bronze S3 location.

**Skills locked in (core):** Python-based ingestion, dlt resource/source/pipeline model, raw/staging layer pattern, merge write-disposition vs. manual upsert SQL, destination-parameterized pipeline design, schema drift handling, source freshness testing.

**Skills locked in (bonus, when revisited):** Iceberg table format and REST catalog mechanics, S3/IAM setup, storage-layer portability (multiple engines reading one physical dataset), incremental loading with a real cursor column (deferred to Statcast).

---

#### Phase 5 — Orchestration and Observability (~1 week core, bonus extends it)

**Core goal:** An explicit, scheduled dependency between the dlt loader and `dbt build` — a GitHub Actions cron job satisfies this functionally. Wire up Elementary and Slack alerts; deliberately break something.

**Key notes (core):**
- Elementary: run `edr report` after dbt builds; configure Slack alerts for failures
- Add dbt source freshness checks — stale dlt syncs surface as pipeline failures

**Bonus-track note:** Asset-based orchestration (Dagster OSS, Prefect Cloud free Hobby tier, or dbt Projects on Snowflake) buys lineage visualization, backfills, sensors, and run-history UI over a plain cron job — genuinely useful concepts, not required for a working pipeline. Dagster Cloud removed free credits from Solo/Starter plans May 1, 2026, so Dagster OSS or Prefect Cloud free tier are the candidates if/when this gets picked up. Also weigh dbt Projects on Snowflake (native Git-connected dbt execution inside Snowflake) as a fourth option — explored but not adopted in Phase 3.

**Skills locked in (core):** Scheduled runs, explicit pipeline dependency, failure alerting, data observability, incident response.

**Skills locked in (bonus):** Asset-based orchestration, dependency-graph visualization, backfills.

---

#### Phase 6 — Semantic Layer (~2 weeks) — CORE, elevated from earlier draft

**Goal:** Define MetricFlow semantic models and metrics; create Snowflake Semantic Views on top of the mart layer. This is the project's most differentiating deliverable, not a nice-to-have.

**Key notes:**
- MetricFlow YAML is the OSI v1.0 reference implementation
- **Self-serve BI tool decision (was: Cube + Evidence by default, now open):** Cube's API-exposure model doesn't actually give a non-technical person a click-around self-serve experience. Decide between: (a) Lightdash — dbt-native metrics, genuine point-and-click explorer, but self-hosting needs Docker; (b) Metabase — no Docker, but metrics live in Metabase, not dbt; (c) keep Cube + Evidence if the API-first pattern is still worth demonstrating on its own. Not yet decided — see Key Architectural Decisions.
- **New core-path artifact:** the public self-serve demo — Evidence's Universal SQL (DuckDB-WASM) over exported Parquet snapshots of the mart/metrics layer, deployed to GitHub Pages, zero backend. This is a separate, lower-effort thing from the internal BI tool decision above and could land earlier than the rest of this phase.

**Skills locked in:** MetricFlow YAML, Snowflake Semantic Views, governed-metrics-to-BI-consumption workflow, in-browser analytical engines (DuckDB-WASM) for zero-infra public data apps.

---

#### Phase 7 — AI Layer (~$5–10/month API, ~2 weeks) — bonus track

**Goal:** Query the semantic layer with natural language via Snowflake Cortex Analyst and Claude API; explore MCP for direct semantic layer access from Claude Code.

**Key notes:**
- Set a $10/month spend cap in Anthropic account settings before writing any API calls
- Compare Snowflake Cortex Analyst vs Claude API over Cube
- Cube has an MCP server — query the semantic layer directly from Claude Code terminal
- **Added June 2026 — parallel sandbox exploration:** MotherDuck Dives lets an AI agent build live, shareable React visualizations over data in MotherDuck via MCP, in public preview since Feb 2026. Worth trying for fun against a throwaway snapshot of the mart layer — not a stack decision, since it requires data living in MotherDuck (reopens the third-engine question already closed for production purposes) and MotherDuck isn't free long-term.

**Skills locked in:** AI-over-data patterns, text-to-metric vs text-to-SQL, semantic layer as AI context, API spend management, MCP orchestration.

---

#### Phase 8 — CI/CD and Portfolio (~1 week) — CORE, pulled forward

**Goal:** Implement slim CI with state-based selection; add MetricFlow validation; write a comprehensive README; record a walkthrough of the full stack end-to-end. Pulled forward relative to earlier sequencing since it's cheap, high-leverage, and doesn't depend on bonus-track work finishing.

**Key notes:**
- Slim CI: `dbt build --select state:modified+` on PRs only
- Create a dedicated CI Snowflake warehouse for isolated cost tracking
- Revisit dbt State (announced June 2026) as a potential platform-managed alternative

**Skills locked in:** Slim CI, multi-environment warehouse management, metric validation in CI, portfolio documentation.

---

### Session Handoff

*Update this at the end of every working session.*

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

**Next actions, superseded below — see "This session (June 2026)" for the current list.**

**Decisions made this session not captured elsewhere:**
- No new phase number for "DuckDB-first dev workflow" — it's a discipline applied within Phase 4, not a separate phase
- Two-role default for day-to-day Snowsight use (`SYSADMIN` default, `ACCOUNTADMIN` for account-level only) — full four-role rotation judged as enterprise ceremony not worth it solo
- Snowflake Optima Metadata (automatic pruning metadata for high-frequency query patterns) noted as existing but not relevant at current hobby-project query volume

---

**Session (June 2026) — Phase 4 dlt pipeline, `games` resource built end-to-end:**
- Cleared remaining Phase 3 wrap-up debt: confirmed `DEFAULT_ROLE = SYSADMIN`; flipped local `profiles.yml` target to `dev_duck`; full `dbt build` verified passing clean against DuckDB (hit and fixed the classic relative-`DUCKDB_PATH` decoy-file bug along the way — see Local Environment notes)
- Installed `dlt==1.28.1` with `[duckdb,snowflake]` extras; confirmed via `pyproject.toml`, not just a clean install message
- Created `feature/dlt-games-pipeline`; removed `load_mlb_data.py` via `git rm`; built `mlb_pipeline.py` from scratch — `games` resource (merge write-disposition, `game_pk` primary key, completed-games-only filter), `mlb_stats_api` source, `--destination duckdb|snowflake` CLI flag (default `duckdb`)
- Hit and resolved the dlt table-ownership collision (pre-existing `raw.games` table from the old manual loader couldn't accept dlt's tracking columns) — deleted `dev.duckdb`, let dlt recreate the table cleanly
- End-to-end verified: 729 completed games loaded across 2022–2026, confirmed live by re-running minutes apart and watching the 2026 count tick up as real games finished
- Hit, diagnosed, and fixed two real test failures the larger dataset surfaced: `accepted_values` on `season` (needed 2025/2026 added — mechanical fix), and `unique` failures on `dim_teams`/`dim_venues` (real cause — team/venue renames over time; user independently verified the Athletics name change in `stg_games` directly via DuckDB CLI before accepting the fix)
- Full `dbt build` passing 48/48 against dlt-sourced DuckDB data
- Installed DuckDB CLI (`brew install duckdb`) as the preferred path for ad hoc local queries — user doesn't use DBeaver day-to-day despite it being installed
- **Found and corrected a real documentation/reality gap:** CLAUDE.md's Phase 3 checklist and CI Architecture Notes both claimed a dual-job (DuckDB + Snowflake) CI setup with GitHub Secrets already configured. Actual `ci.yml` on `main` only has a single DuckDB-only job. Corrected throughout this doc — see CI Architecture Notes and Phase 4.

**Decisions made this session, not fully captured in Part 1 prose:**
- `games` resource deliberately excludes Scheduled/In Progress games — completed-games-only is the chosen scope for the core path, not a placeholder
- `games` does not use `dlt.sources.incremental()` — full-season re-pull + merge fits this source's shape better; the real incremental cursor pattern is deferred to Statcast, where it'll actually be needed
- dlt pipeline destination is a CLI flag, not hardcoded, specifically so DuckDB can be refreshed freely (real data, zero cost) independent of Snowflake spend
- `dim_teams`/`dim_venues` use most-recent-name-wins (ranked by `game_date desc`) rather than full SCD-style history tracking — simplest correct option for the core path, revisit only if a future phase needs historical name lookups

**Active branch (as of that session):** `feature/dlt-games-pipeline` — since confirmed merged to `main` (see the July 2026 session below). Three known blockers at the time:
1. `ci.yml`'s DuckDB job still calls deleted `load_mlb_data.py` — needs to call `mlb_pipeline.py --destination duckdb` — **resolved before merge**
2. Snowflake `RAW.GAMES` still has the Phase 3 manual-CSV-stopgap table; first `--destination snowflake` run will hit the same table-ownership collision DuckDB hit — needs the table dropped first — **resolved in the July 2026 session below**
3. CI's Snowflake-on-merge job doesn't exist yet (secrets + second job definition + push-trigger) — currently scoped as its own follow-up session, not a quick add-on — **still open, see below**

**Next actions, superseded below — see "Session (July 2026)" for the current list.**

When Phase 6 starts: decide Lightdash vs. Metabase vs. keeping Cube+Evidence for the internal self-serve BI question.

---

**Session (July 2026) — Real Snowflake load, secrets consolidation, third RBAC gotcha:**
- Confirmed `feature/dlt-games-pipeline` was merged to `main` at some point after the last documented session — `ci.yml` already correctly calls `mlb_pipeline.py --destination duckdb`, and `mlb_pipeline.py` exists on `main`. Blocker #1 above was already resolved; this doc's "Known open items" list just hadn't been updated to reflect it.
- Dropped the Phase 3 manual-CSV-stopgap `RAYS_ANALYTICS.RAW.GAMES` table (owned by `ACCOUNTADMIN`) to let dlt recreate it cleanly, owned by `SYSADMIN` this time
- Hit the Snowflake credentials gap for dlt (a separate config store from dbt's `profiles.yml`). Instead of adding a `.dlt/secrets.toml`, consolidated to a single `.env` at repo root, read natively by both dlt (`DESTINATION__SNOWFLAKE__CREDENTIALS__*` env vars) and dbt (`profiles.yml` via `env_var()`) — see Key Architectural Decisions
- Hit and resolved the third instance of the `ACCOUNTADMIN`/`SYSADMIN` ownership gotcha, this time at the schema level (missing `CREATE TABLE` privilege on `SCHEMA RAW`) — see Role Hierarchy & Privilege Notes
- Real `--destination snowflake` run succeeded: ~740 completed games loaded into `RAYS_ANALYTICS.RAW.GAMES`, verified via `INFORMATION_SCHEMA.TABLES` (owner now `SYSADMIN`, row count and season range confirmed)

**Active branch:** `chore/consolidate-secrets-env` — not yet merged. Both the `.env` file and the `profiles.yml` edit live outside the repo (gitignored / outside version control by design), so this branch's only actual diff is this CLAUDE.md update.

**Next actions:**
1. Commit this CLAUDE.md update and merge `chore/consolidate-secrets-env`
2. Build the Snowflake-on-merge CI job — GitHub Secrets, a `push`-gated second job, dynamic Snowflake `profiles.yml` generation in CI (the one remaining Phase 4 blocker — see CI Architecture Notes)
3. Begin the Statcast/pybaseball resource — first real test of dlt's `incremental()` cursor pattern, since `games`' full-repull approach won't fit that data's volume