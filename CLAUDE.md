# Rays Analytics — Project Instructions

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

My name is Dyllyn Giles, based in Lexington, Kentucky. I came in with dbt and BI experience but no hands-on modern cloud warehouse experience — this project is where that's been built from scratch. Goal: a complete, portfolio-ready modern ELT stack for learning and career development. I prefer to understand what I'm doing rather than just following commands.

**Why I'm actually doing this project:** curiosity and enjoyment, full stop. Job marketability is real and welcome but not the filter for what's worth exploring — don't gate discussing/prototyping an idea behind "does this earn its place." That scrutiny is for what becomes permanent, maintained stack infrastructure. Default to following interesting tangents.

That said, I still want honest pushback when something is actually unsound, outdated, or solving a problem that doesn't exist — different from ROI-gating, and I want it regardless of how fun the idea sounded. Real constraint I care about: not spending a lot of money. Flag other practical parameters as they come up — ongoing maintenance burden, new credentials meaning new security surface area, and the 16GB RAM ceiling.

I'm also deliberately going deep on platform-specific exploration (Query Profile, role hierarchy, catalog mechanics) on its own terms, not just when strictly needed for the build. Same applies to DuckDB once Phase 4 work resumes.

---

### My Machine

- M4 Mac Mini, 16GB RAM
- macOS, Apple Silicon (aarch64)

---

### Local Environment

- Homebrew (package manager)
- UV 0.11.17 (Python package/environment manager — replaces both pip and pyenv)
- Python 3.12.13 managed by UV
- VS Code with extensions: dbt Power User, Python, GitLens, Claude Code
- GitHub account connected via SSH key (Ed25519)
- tealdeer installed for command reference (`tldr <command>`)
- DBeaver installed but not used — DuckDB CLI is the preferred path for ad hoc local queries
- DuckDB CLI via `brew install duckdb` — invoke as `duckdb <path>`. **Always use the absolute path** (`/Users/dyllyngiles/projects/rays-analytics/dev.duckdb`) — a relative path opens/creates a different, empty file depending on cwd. This bug class has bitten `dbt build` without `DUCKDB_PATH`, the dlt pipeline pre-parameterization, and the CLI itself.

---

### Key Environment Decisions

**UV replaces both pip and pyenv.** No shims, no PATH conflicts, 10–100x faster than pip. `uv add <package>` updates both `pyproject.toml` and `uv.lock` together. Confirmed as the 2026 community standard for analytics engineering.

**Python 3.12.13** was chosen for dbt-snowflake adapter compatibility.

**The virtual environment lives at repo root** — `~/projects/rays-analytics/.venv` — not inside the `rays_analytics/` dbt subfolder. This keeps a single venv accessible to both the loader script and dbt commands without path gymnastics.

**Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`**, both at repo root. Install locally: `uv sync`. Install in CI: `uv sync --locked`.

`--locked` and `--frozen` are not the same thing:
- `--locked`: Resolves dependencies, then **fails if the result would differ from the committed `uv.lock`** — catches drift, the correct CI choice.
- `--frozen`: Skips resolution entirely, installs whatever is in `uv.lock` without checking `pyproject.toml` — faster in deployment, doesn't catch drift.

**Docker is intentionally avoided.** 16GB RAM constraint; entire stack runs as Python or Node processes.

**`profiles.yml` lives at `~/.dbt/profiles.yml`** — never committed. Points to Snowflake DEV schema; DuckDB target retained as `dev_duck`.

**DuckDB path is always relative** (`dev.duckdb`) from repo root, never hardcoded absolute. `DUCKDB_PATH` overrides it in CI.

**UV does not load `.env` files automatically.** Use `uv run --env-file .env <command>` to load them explicitly — works for any command in the venv (e.g. `uv run --env-file .env dbt build`). For scripts needing env vars at import time, use python-dotenv: `from dotenv import load_dotenv; load_dotenv()`.

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
- Phase 4, slimmed: dlt → Snowflake `RAW` directly, no bronze/Iceberg layer
- Phase 5, slimmed: GitHub Actions with an explicit scheduled dependency between loader and `dbt build`, no orchestrator bake-off
- Phase 6, elevated: MetricFlow + Snowflake Semantic Views are core, not optional — the strongest differentiator. Cube's necessity is being reconsidered.
- Phase 8, pulled forward: README + walkthrough
- New, low-effort: a public self-serve demo — Evidence's Universal SQL (DuckDB-WASM) over exported Parquet snapshots, deployed as a static GitHub Pages site. Zero backend/cost/credentials.

**Bonus / platform-depth track (curiosity-driven, no deadline):**
- Bronze layer: S3 + Iceberg + Snowflake Open Catalog, future self-hosted Polaris/Lakekeeper experiment
- Orchestration bake-off: Dagster OSS vs. Prefect vs. dbt Projects on Snowflake
- Deep Snowflake exploration: Time Travel, Zero-Copy Cloning, Cortex, Marketplace, Streamlit
- Phase 7 AI/MCP layer, including a MotherDuck Dives sandbox experiment
- Self-serve BI tool decision: Lightdash (point-and-click, needs Docker) vs. Metabase (no Docker, metrics live outside dbt)

---

**Snowflake-native additions (Phase 3+):**
- dbt Projects on Snowflake (GA November 2025) — native dbt Core inside Snowflake via a Git-connected Workspace + `DBT PROJECT` object. Explored in Phase 3, unconfigured. Deferred to the Phase 5 orchestration decision.
- Snowflake Semantic Views (GA March 2026) — warehouse-native semantic layer, zero extra cost
- Snowflake Cortex Analyst — NL querying over semantic views, ~$5–15/month at hobby scale

**Estimated monthly cost: ~$60–75/month** — Snowflake ~$30–40, Cortex ~$5–15, Claude Pro $20, Anthropic API (Phase 7+) ~$5–10, rest free.

---

### Key Architectural Decisions

Full reasoning and alternatives considered for settled decisions: see CHANGELOG.md.

**Why dlt over Airbyte:** Airbyte is Docker-heavy with an uncertain free tier; dlt teaches ingestion at code level instead of abstracting it behind a UI.

**Why dlt over Snowflake Openflow (resolved June 2026):** Openflow fits its ~20 supported connectors with no customization needed; MLB Stats API and pybaseball/Statcast are bespoke sources outside that list, and Openflow needs real infrastructure (BYOC/Snowpark Container Services) that cuts against the RAM ceiling.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow is the OSI v1.0 reference implementation for semantic layers; Cube provides the API exposure layer dbt Cloud would otherwise lock behind $100/month. See CHANGELOG.md for full reasoning.

**Cube's necessity reconsidered (added June 2026):** Cube exposes governed metrics over an API — it isn't itself a self-serve dashboard tool. MetricFlow + Snowflake Semantic Views stay core regardless; Cube is now optional pending the Phase 6 BI-tool decision.

**Why Dagster OSS or Prefect over Dagster Cloud:** Dagster Cloud removed free credits from Solo/Starter plans May 1, 2026 (per-asset billing from zero, no grandfathering). Dagster OSS locally or Prefect Cloud's free Hobby tier cover the same learning goals at zero cost. See CHANGELOG.md for full reasoning.

**Why S3 + Iceberg + Snowflake Open Catalog over self-hosted Polaris or AWS Glue (decided June 2026; rescoped to bonus track):** Open Catalog is a managed hosting of the actual open-source Apache Polaris, free during the current billing period and reachable by both local dev and CI (unlike self-hosted Polaris on the Mac Mini) while staying open-source-first (unlike AWS Glue). Core Phase 4 skips this entirely — dlt writes straight into Snowflake `RAW`, no bronze layer. Full three-way comparison and reasoning: see CHANGELOG.md.

**Why Evidence over Metabase:** Code-first, Git-native, fits the everything-as-code philosophy. Cube Cloud free tier is dev/test only — Cube Core runs as a local Node process at zero cost if needed.

**Public self-serve demo, added June 2026:** Evidence ships a DuckDB engine to the browser via WebAssembly (Universal SQL) — a static GitHub Pages site built from exported Parquet snapshots lets any visitor run live SQL client-side, no backend/credentials/per-visitor cost. Separate from the internal BI decision below. Perspective (FINOS) is the fallback if drag-and-drop pivoting matters more than filter-driven interactivity.

**Self-serve BI tool decision, added June 2026, deferred to Phase 6:** Lightdash reads metrics directly from dbt YAML for a genuine point-and-click explorer, but self-hosting needs Docker (conflicts with no-Docker stance) vs. Metabase (no Docker, but metrics live outside dbt). Not yet decided.

**dlt resource design for `games` — completed games only, no live/in-progress state (decided June 2026):** The `games` resource filters to `Final`/`Completed Early` before yielding, so unplayed or in-progress games never reach `raw.games` — a deliberate scope call, not a technical limitation. Full reasoning: see CHANGELOG.md.

**Why `games` doesn't use dlt's `incremental()` cursor (decided June 2026):** The schedule endpoint doesn't expose a true modified-since cursor and returns the whole season every call regardless, so `games` uses full-season re-pull + `merge` write-disposition keyed on `game_pk` instead. **This will not hold at Statcast scale** — see Phase 4 notes; pitch-level data has real cursor potential (game date) and re-pulling full history every run isn't viable at that volume. Full reasoning: see CHANGELOG.md.

**dlt pipeline destination is parameterized, not hardcoded (decided June 2026):** `mlb_pipeline.py` takes `--destination duckdb|snowflake` as a CLI flag (default `duckdb`). Only the `pipeline.run()` destination argument changes — chosen so DuckDB refreshes freely at zero cost while Snowflake compute is only spent when explicitly requested. CI's DuckDB and Snowflake jobs will call the same script with different flags.

**dlt table ownership gotcha (hit June 2026, again on Snowflake July 2026):** dlt cannot retrofit its tracking columns (`_dlt_id`, `_dlt_load_id`) onto a table it didn't create (DuckDB: `Parser Error: Adding columns with constraints not yet supported`). Fix: any table dlt owns must be created by dlt from a clean slate — drop it and let the pipeline recreate it.

**`dim_teams`/`dim_venues` deduplication — most-recent-name-wins (decided June 2026):** Team/venue names can change over time for the same numeric id (relocation, sponsorship renames), which broke a plain `(id, name)` dedup. Fixed by ranking rows per id by `game_date desc` and keeping only the most recent name. Full reasoning and alternatives considered: see CHANGELOG.md.

**Secrets consolidation — single `.env` shared by dbt and dlt, no `.dlt/secrets.toml` (decided July 2026):** dlt and dbt each kept a separate credential store for the same Snowflake account/service user. Both now read one gitignored `.env` at repo root: dlt via `DESTINATION__SNOWFLAKE__CREDENTIALS__*` env vars, dbt via `env_var()` in `profiles.yml` (see Current `profiles.yml` structure below). GitHub Secrets for CI stay a separate third location. Full reasoning: see CHANGELOG.md.

**Why 16GB Mac Mini is sufficient:** Docker has been removed from the stack entirely. All tools run as Python or Node processes. No containers.

**Why GitHub Actions cron stays for Statcast, rather than pulling Dagster/Prefect forward from the bonus track (decided July 2026):** GitHub Actions cron has gotten measurably less reliable in 2026 (scheduler delays since February; auto-disables scheduled workflows after 60 days of repo inactivity — a real risk during MLB's off-season). The `games` resource is unaffected — it re-pulls the full season every run, so a missed firing self-heals. Statcast's incremental cursor won't have that property; a missed run there creates a silent watermark gap. Fix is not a new orchestrator but a `dbt source freshness` check + alert (already in the Phase 5 core plan) plus a `workflow_dispatch:` manual-fallback trigger, both landing before Statcast ships. Revisit Dagster OSS/Prefect Cloud only if this mitigation proves insufficient in practice.

**Why Workload Identity Federation (WIF) over key-pair-in-Secrets for the CI dbt job (decided July 2026):** see Workload Identity Federation (WIF) Notes below for full reasoning, setup, and gotchas. Short version: Snowflake and `dbt-snowflake` both now support it, it removes a stored secret entirely, and the trust binding is scoped tighter than a key-pair ever could be. dlt has no equivalent yet — a known asymmetry for when Phase 5 puts the loader itself into CI.

**dbt Core vs dbt Fusion vs dbt Core v2.0:** dbt Labs open-sourced the Fusion runtime as dbt Core v2.0 under Apache 2.0 at Summit June 2026. v2.0 is alpha; dbt Core v1.11.x remains the right choice for now. dbt Core v1.12 (beta) ships the same Fusion parser via `dbt parse --use-v2-parser` as a dry-run compatibility check. Revisit at Phase 8.

**Snowflake-native dbt:** GA November 2025. No additional licensing cost — pay only warehouse credits. Worth exploring alongside the local dbt workflow in Phase 3.

**Snowflake Semantic Views:** Standard SQL querying GA March 2026. Zero extra cost, zero infrastructure overhead. Snowflake-only, but this stack is Snowflake-only in production.

**dbt/Fivetran merger:** Completed June 1, 2026 (Fraser CEO, Handy President). dbt Core remains Apache 2.0; no impact on this stack. Long-term Core-vs-commercial investment balance bears watching.

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
| MotherDuck | Third portability target considered June 2026; deprioritized — work-related interest, not project-specific |
| AWS Glue | Considered for the Iceberg catalog; zero-ops but proprietary |
| Airflow | Common in AE postings but not required — concepts transfer from Dagster/Prefect |

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
- **Account identifier:** stored locally in `~/.dbt/profiles.yml`
- **Warehouse:** COMPUTE_WH (X-Small, 60-sec auto-suspend, auto-resume on)
- **Resource monitor:** MONTHLY_SPEND_CAP — 15 credits/month, notify at 75%, suspend at 100%
- **Database:** RAYS_ANALYTICS — **Schemas:** RAW, DEV, PROD
- **Service user:** DBT_SERVICE_USER — TYPE = SERVICE, SYSADMIN role, key-pair auth. Key: `~/.ssh/dbt_service_user_rsa_key_p8.pem` (PKCS#8)
- **CI service user:** RAYS_ANALYTICS_CI_SERVICE — TYPE = SERVICE, SYSADMIN role, WIF (OIDC) auth, no key-pair — see WIF Notes below

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

### Workload Identity Federation (WIF) Notes

**Decision (July 2026):** the Snowflake-on-merge CI job authenticates via WIF (OIDC), not key-pair-in-GitHub-Secrets. Snowflake's WIF reached GA August 2025, and `dbt-snowflake` gained WIF support via a PR merged May 20, 2026. Snowflake recommends WIF so no long-lived secret sits in CI; key-pair is now the fallback. No private key or GitHub Secret to manage — trust is scoped to `repo:dyllyngiles/rays-analytics:ref:refs/heads/main` at the identity layer, so a PR-branch workflow can't authenticate as this user regardless of trigger conditions.

**Important asymmetry — dlt does not support WIF.** dlt's Snowflake destination exposes only password/key-pair/OAuth/Snowpark-OAuth-token auth, even though the underlying driver has supported WIF since v4.0. Doesn't block the current CI job (dbt-only), but the Phase 5 cron job (which also runs dlt) will be split-auth: `dbt build` secretless via WIF, dlt still needing key-pair credentials in GitHub Secrets.

**Snowsight setup, completed (pure account-side config):**
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

Confirmed via `DESCRIBE USER RAYS_ANALYTICS_CI_SERVICE` (`HAS_WORKLOAD_IDENTITY: true`) and:
```sql
SELECT * FROM TABLE(
  INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME => 'RAYS_ANALYTICS_CI_SERVICE',
    REF_ENTITY_DOMAIN => 'USER'
  )
);
```

**New gotchas hit while setting this up (distinct from the ACCOUNTADMIN/SYSADMIN ownership pattern below):**
- `CREATE USER` and `CREATE AUTHENTICATION POLICY` are `SECURITYADMIN`/`USERADMIN` territory, not `SYSADMIN` — a different branch of the hierarchy, not another ownership-gotcha instance. See the domain table in Role Hierarchy & Privilege Notes below.
- **`DEFAULT_ROLE` on `CREATE USER` doesn't grant the role** — only sets what activates by default *if* the user already holds it. `SHOW GRANTS TO USER` came back empty until `GRANT ROLE SYSADMIN TO USER ...` ran explicitly — no error, just a silently empty grant set.
- **`AUTHENTICATION POLICY` is schema-scoped, not account-level** — needs `CREATE AUTHENTICATION POLICY` granted on that specific schema. Namespaced inside `RAW` for now (a security object living in a data schema); worth moving to a dedicated schema later, not urgent.
- **`ALTER USER ... SET AUTHENTICATION POLICY` takes no `=`** — the policy name follows the keywords directly.
- **`DESCRIBE USER` doesn't surface authentication-policy attachment** — use `INFORMATION_SCHEMA.POLICY_REFERENCES` instead.

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
`ACCOUNTADMIN` inherits `SYSADMIN` and `SECURITYADMIN`'s privileges, not the reverse. `ORGADMIN` is a separate org-level role for managing multiple accounts; mostly irrelevant here except **`ORGADMIN` is required to create a Snowflake Open Catalog account** (see Bronze Layer notes below).

**Domain split, worth internalizing (added July 2026):** the recurring confusion isn't about `ACCOUNTADMIN` vs. lower roles — it's two separate branches of the hierarchy each owning a different *kind* of thing:

| Role | Domain | Covers |
|---|---|---|
| `SYSADMIN` | Data & compute objects | Databases, schemas, tables, warehouses |
| `SECURITYADMIN` (and its child `USERADMIN`) | Identity & access | Users, roles, grants, authentication policies, network policies |
| `ACCOUNTADMIN` | Account-level only | Billing, account parameters, replication, org settings |

Litmus test: *who/what can authenticate* → `SECURITYADMIN`. *Data/compute objects* → `SYSADMIN`. `ACCOUNTADMIN` inherits both, which is why it "just works" regardless of domain — and why it's worth resisting as a default, since it papers over which branch actually owns a task.

**Default role decision:** `SYSADMIN` is the default Snowsight role going forward, not `ACCOUNTADMIN`. Set via:
```sql
ALTER USER <username> SET DEFAULT_ROLE = SYSADMIN;
```
`ACCOUNTADMIN` is reserved for genuinely account-level tasks: resource monitors, billing, rare service-account/user management. Full four-role rotation is enterprise ceremony not worth it solo — two roles is right-sized here.

**The gotcha (bit three times — twice in Phase 3, once in Phase 4):** anything created via Snowsight UI is owned by whatever role the session defaults to. If that's `ACCOUNTADMIN` and `DBT_SERVICE_USER` runs as `SYSADMIN`, `SYSADMIN` has zero automatic access. Hit at three object levels — table, warehouse, schema — each with a distinct error. Full story with exact error text: see CHANGELOG.md.

**Fix, any case:** grant the missing privilege explicitly, run as the object's owning role:
```sql
GRANT SELECT ON TABLE RAYS_ANALYTICS.RAW.GAMES TO ROLE SYSADMIN;
GRANT USAGE, OPERATE ON WAREHOUSE COMPUTE_WH TO ROLE SYSADMIN;
GRANT CREATE TABLE ON SCHEMA RAYS_ANALYTICS.RAW TO ROLE SYSADMIN;
```
Better long-term fix: switch the Snowsight role selector to `SYSADMIN` *before* any manual UI work, so objects are owned right from creation. One upside of the schema-level grant: `SYSADMIN` now owns whatever it creates in `RAW` going forward — no more retroactive grants needed there.

---

### Bronze Layer & Iceberg Catalog Notes

Bonus-track, not actively worked. Architecture (when revisited): raw data lands in S3 (us-east-2) as Iceberg tables, cataloged through Snowflake Open Catalog, with Snowflake and DuckDB both reading the same physical location as separate engines. Deferred, not rejected — self-hosted Polaris is a low-friction switch later since Open Catalog runs the identical software. Full setup requirements, cost, single-writer rule, and catalog comparison: see CHANGELOG.md.

---

### Snowsight Navigation (as of June 2026)

Snowflake reorganized nav into top-level categories: Projects, Ingestion, Transformation, AI & ML, Monitoring, Marketplace, Catalog, Data sharing, Governance & security, Compute, Admin.

Confirmed mappings (old → new):
- **Data → Databases** → **Catalog → Database Explorer**
- **dbt Projects** → **Transformation → dbt projects** (not nested under Workspaces)
- **Query History**/Query Profile stayed put: **Monitoring → Query History**
- **SQL editor:** Projects → Workspaces (renamed from Worksheets, April 20, 2026; legacy Worksheets removed June 22, 2026)

**Caveat:** this UI shifts often enough that exact paths shouldn't be trusted long-term without a re-check. Treat as "true as of June 2026," not permanent.

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

Snowflake credential fields are all `env_var()` calls pulled from a single gitignored `.env` at repo root that dlt also reads natively (see "Secrets consolidation"). `schema: DEV` stays hardcoded deliberately — dbt-only config, not a shared credential.

---

### Project Structure

```
~/projects/rays-analytics/     ← project root, Python scripts, git repo
  .venv/                       ← venv (repo root, NOT in rays_analytics/)
  pyproject.toml, uv.lock      ← dependencies
  mlb_pipeline.py              ← dlt pipeline, MLB Stats API → DuckDB/Snowflake (--destination flag)
  dev.duckdb                   ← local DuckDB file (gitignored)
  .env                         ← Snowflake creds shared by dbt + dlt (gitignored)
  publish_docs.sh              ← publishes dbt docs to GitHub Pages
  CLAUDE.md, CHANGELOG.md
  .github/workflows/ci.yml     ← CI — runs on every PR to main
  rays_analytics/               ← dbt project, all dbt commands run from here
    models/
      staging/  sources.yml, schema.yml, stg_games.sql
      marts/    schema.yml, dim_teams.sql, dim_venues.sql, fct_games.sql
```

---

### Data Model

- **Source:** MLB Stats API (no auth required)
- **Raw table:** `RAYS_ANALYTICS.RAW.GAMES` in Snowflake — populated by `mlb_pipeline.py` (`--destination snowflake`), owned by `SYSADMIN`. Phase 3 manual-CSV-stopgap table fully retired.
- **Rays team ID:** 139
- **Seasons loaded:** 2022–2026 (~740 completed games; 162 each for 2022–2025, 92 for the still-in-progress 2026 season, growing run-over-run)
- **Star schema:** stg_games → dim_teams, dim_venues, fct_games
- **48 tests** — not_null, unique, accepted_values, relationships

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
- Python scripts run from project root, not the dbt subfolder
- Never hardcode absolute file paths in Python scripts — use `os.getenv('VAR', 'relative/default')`
- Default Snowsight role is `SYSADMIN`, not `ACCOUNTADMIN` — switch explicitly only for resource monitors, billing, or service-account management
- `git config --global fetch.prune true` is set — merged feature branches don't linger as stale tracking refs
- GitHub has "automatically delete head branches" enabled — local branches still need an explicit `git branch -d` after
- Pull past PR descriptions with `gh pr list --state all` then `gh pr view <number>` (`--json body -q .body` for just the text)
- **Repo audited clean (June 2026):** confirmed via `git ls-files` and `git log --all --oneline -- profiles.yml '*.pem' '*.key' '*.env'` (empty). Worth re-running periodically.
- **One-off exports never get committed.** `.gitignore` includes `/games_export.csv` and `/scratch/` for throwaway dumps — delete when done or park in `/scratch/`.

---

### CI Architecture Notes

The GitHub Actions workflow (`.github/workflows/ci.yml`) currently has **one job**, triggered on `pull_request` to `main` only. It runs `dbt build` against DuckDB, first calling `mlb_pipeline.py --destination duckdb` to populate the local database.

**Target architecture (Snowflake side built; `ci.yml` not yet touched):** a second job, gated to `push` on `main` (post-merge), running `dbt build` against real Snowflake. **Revised July 2026 to use WIF instead of key-pair-in-Secrets** — see WIF Notes above. `RAYS_ANALYTICS_CI_SERVICE`, its `SYSADMIN` grant, and its OIDC trust policy are already created in Snowsight. The runner's dynamically-generated `profiles.yml` will carry only non-secret identifiers (`authenticator: workload_identity`) — no private key material anywhere in the workflow. DuckDB stays on every PR, bounding Snowflake compute to "once per merged PR."

Remaining work, inside `ci.yml` (needs a branch): a second job with a `push`-only trigger, a `permissions: id-token: write` block plus an OIDC-token-fetch step, and a Snowflake `profiles.yml` generation step parallel to the DuckDB one. Confirm and pin the `dbt-snowflake` version that shipped WIF support (PR merged May 20, 2026). Not yet started.

**Known asymmetry to carry into Phase 5:** dlt has no WIF support (see WIF Notes) — when the dlt loader itself eventually runs in CI (the Phase 5 cron job), that job will need key-pair credentials in GitHub Secrets for the dlt step even though the dbt step alongside it stays secretless.

**Actions pinning:** All actions pinned to exact commit hashes, not floating tags — the March 2025 tj-actions/changed-files compromise (secrets leaked via a hijacked tag) is the canonical reason. Current pinned hashes:
- `actions/checkout` v6.0.2 → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `astral-sh/setup-uv` v8.1.0 → `08807647e7069bb48b6ef5acd8ec9567f424441b`

**Dependency installation:** `uv sync --locked` — verifies `uv.lock` is consistent with `pyproject.toml` and fails if they've drifted.

**Dependency auditing:** `uv audit` runs as a CI step. Built into uv 0.10.12+, no additional install required.

**`uv audit` can fail a PR for reasons unrelated to that PR** — it audits whatever's pinned in `uv.lock`, so a newly-disclosed CVE against an already-resolved dependency can fail an unrelated change (hit on a docs-only PR — `cryptography`/`msgpack`). Fix is a narrow lockfile bump:
```bash
uv lock --upgrade-package cryptography --upgrade-package msgpack
uv sync --locked
```
Run from repo root, not the `rays_analytics/` subfolder — `uv.lock` lives at root.

**UV version:** Pinned to `0.11.17` to match local version exactly.

---

### Learning Roadmap

#### Phase 1 — Foundation ✅ COMPLETE

**Skills locked in:** dbt project structure, staging/mart layering, testing discipline, star schema dimensional modeling, feature branch git workflow.

---

#### Phase 2 — Version Control ✅ COMPLETE

**Skills locked in:** Git-based workflow, CI pipeline authoring, PR-driven development, branch protection, secrets management discipline, dependency auditing.

---

#### Phase 3 — Real Warehouse ✅ COMPLETE

**Goal:** Swap the dbt adapter from DuckDB to Snowflake, port all models, configure dev/prod, establish cost controls. Full completed-items checklist: see CHANGELOG.md.

**Skills locked in:** Snowflake architecture, cost monitoring, key-pair authentication, dbt-snowflake adapter setup, dual-environment CI design, Snowflake RBAC hierarchy and privilege troubleshooting, reading a Query Profile, Snowsight navigation literacy.

---

#### Phase 4 — Ingestion (~1 week, slimmed for core path) — IN PROGRESS

**Resolved June 2026:** dlt over Openflow — see Key Architectural Decisions. No longer a blocking pause.

**Core goal:** Replace `load_mlb_data.py` with a proper dlt pipeline writing directly into `RAYS_ANALYTICS.RAW`; add Statcast data via pybaseball; build staging models over dlt raw output; implement incremental loading. **No bronze/Iceberg layer in this pass.**

Full completed-items lists (June and July 2026 sessions): see CHANGELOG.md.

**Known open items:**
- CI dual-job architecture (Snowflake-on-merge) — Snowflake-side setup done (WIF service user, role grant, auth policy); `ci.yml` changes not yet started — see CI Architecture Notes. Last remaining Phase 4 blocker.
- Statcast/pybaseball resource not yet started — needs the `dbt source freshness` check/alert and a `workflow_dispatch:` fallback trigger first (see cron reliability decision above)

**Key notes:**
- Incremental loading needs a cursor column. `games` does NOT use `dlt.sources.incremental()` (see Key Architectural Decisions); Statcast will need the real cursor pattern.
- Deliberately introduce a schema change and observe dlt/dbt source freshness response — not yet done

**Bonus-track note (when revisited):** S3 + Iceberg + Snowflake Open Catalog bronze layer — dlt writes once to S3, Snowflake/DuckDB read from that location as separate engines. Setup: `ORGADMIN`-created Open Catalog account, S3 bucket, scoped IAM credentials. Single-writer discipline applies.

**Skills locked in (core):** Python-based ingestion, dlt resource/source/pipeline model, raw/staging layer pattern, merge write-disposition, destination-parameterized pipeline design, schema drift handling.

**Skills locked in (bonus, when revisited):** Iceberg format and REST catalog mechanics, S3/IAM setup, storage-layer portability, incremental loading with a real cursor.

---

#### Phase 5 — Orchestration and Observability (~1 week core, bonus extends it)

**Core goal:** An explicit, scheduled dependency between the dlt loader and `dbt build` — a GitHub Actions cron job satisfies this functionally. Wire up Elementary and Slack alerts; deliberately break something.

**Key notes (core):**
- Elementary: run `edr report` after dbt builds; configure Slack alerts for failures
- Add dbt source freshness checks — stale dlt syncs surface as pipeline failures
- **Decided July 2026: this freshness check + alert must land before Statcast, not after.** GitHub Actions cron stays as the scheduler (see Key Architectural Decisions for the full reasoning) — the freshness check is what makes a missed/delayed run visible instead of silently absorbed once Statcast's real incremental cursor is in play. Add `workflow_dispatch:` alongside `schedule:` on the cron job at the same time, as a manual fallback.

**Bonus-track note:** Asset-based orchestration (Dagster OSS, Prefect Cloud free Hobby tier, or dbt Projects on Snowflake) buys lineage visualization, backfills, sensors, and run-history UI over a plain cron job — genuinely useful, not required. Dagster OSS or Prefect Cloud free tier are the candidates if this gets picked up.

**Skills locked in (core):** Scheduled runs, failure alerting, data observability.

**Skills locked in (bonus):** Asset-based orchestration, dependency-graph visualization, backfills.

---

#### Phase 6 — Semantic Layer (~2 weeks) — CORE, elevated from earlier draft

**Goal:** Define MetricFlow semantic models and metrics; create Snowflake Semantic Views on top of the mart layer. This is the project's most differentiating deliverable, not a nice-to-have.

**Key notes:**
- MetricFlow YAML is the OSI v1.0 reference implementation
- **Self-serve BI tool decision (was: Cube + Evidence by default, now open):** decide between Lightdash, Metabase, or keep Cube + Evidence — see Key Architectural Decisions.
- **New core-path artifact:** the public self-serve demo (Evidence Universal SQL over Parquet, GitHub Pages) — separate, lower-effort, could land earlier than the rest of this phase.

**Skills locked in:** MetricFlow YAML, Snowflake Semantic Views, governed-metrics-to-BI workflow, in-browser analytical engines (DuckDB-WASM).

---

#### Phase 7 — AI Layer (~$5–10/month API, ~2 weeks) — bonus track

**Goal:** Query the semantic layer with natural language via Snowflake Cortex Analyst and Claude API; explore MCP for direct semantic layer access from Claude Code.

**Key notes:**
- Set a $10/month spend cap in Anthropic account settings before writing any API calls
- Compare Snowflake Cortex Analyst vs Claude API over Cube; Cube has an MCP server for querying the semantic layer from Claude Code
- **Parallel sandbox exploration:** MotherDuck Dives (AI-built React viz over MotherDuck via MCP) — worth trying for fun against a throwaway snapshot, not a stack decision.

**Skills locked in:** AI-over-data patterns, text-to-metric vs text-to-SQL, semantic layer as AI context, MCP orchestration.

---

#### Phase 8 — CI/CD and Portfolio (~1 week) — CORE, pulled forward

**Goal:** Implement slim CI with state-based selection; add MetricFlow validation; write a comprehensive README; record a walkthrough of the full stack end-to-end. Pulled forward relative to earlier sequencing since it's cheap, high-leverage, and doesn't depend on bonus-track work finishing.

**Key notes:**
- Slim CI: `dbt build --select state:modified+` on PRs only
- Create a dedicated CI Snowflake warehouse for isolated cost tracking
- Revisit dbt State (announced June 2026) as a potential platform-managed alternative

**Skills locked in:** Slim CI, multi-environment warehouse management, metric validation in CI, portfolio documentation.

---

### Current Status

**Active branch:** `chore/split-claude-md-changelog` (split this doc into a slim current-state CLAUDE.md + CHANGELOG.md)

**Next actions:**
1. Open a feature branch for `ci.yml`: second job (`push`-to-`main` trigger, `permissions: id-token: write`, OIDC-token-fetch step, dynamic Snowflake `profiles.yml` using WIF) — the last Phase 4 blocker, see CI Architecture Notes
2. Confirm and pin the exact `dbt-snowflake` version that shipped WIF support, then merge, closing Phase 4
3. Before Statcast: add the `dbt source freshness` check/alert and `workflow_dispatch:` fallback trigger to the cron job
4. Begin the Statcast/pybaseball resource — first real test of dlt's `incremental()` cursor pattern
5. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence

Full session-by-session history: see CHANGELOG.md.
