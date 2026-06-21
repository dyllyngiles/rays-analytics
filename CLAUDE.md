# Rays Analytics — Project Instructions

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

My name is Dyllyn Giles. I'm based in Lexington, Kentucky. I work in analytics with some dbt experience but no modern cloud warehouse experience. My goal is to build a complete, portfolio-ready modern ELT stack for learning and career development. My personal knowledge system is a pencil and notebook. I prefer to understand what I'm doing rather than just following commands.

**Why I'm actually doing this project:** curiosity and enjoyment, full stop. Job marketability and patterns transferable to my day job are real and welcome, but they are not the filter for what's worth exploring. Don't gate discussing, exploring, or prototyping an idea behind "does this earn its place" — that scrutiny is for decisions about what becomes permanent, maintained stack infrastructure, not for whether something's worth looking at. Default to following interesting tangents.

That said, I still want honest pushback when something is actually unsound, outdated, or solving a problem that doesn't exist — that's different from ROI-gating, and I want it regardless of how fun the idea sounded going in. Real constraint I do care about: I'm not trying to spend a lot of money. Feel free to flag other practical parameters as they come up — ongoing maintenance burden (separate from whether something's resume-worthy), new credentials meaning new security surface area, and the 16GB RAM ceiling on my machine are the ones that have come up so far.

I'm also deliberately trying to soak up hands-on Snowflake experience while I have access to it — I'm not sure I'll get to use it professionally again, so going deep on platform-specific exploration (Query Profile, role hierarchy, catalog mechanics) is worth it on its own terms, not just when it's strictly needed for the build. Same applies to DuckDB once Phase 4 work resumes.

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
- DBeaver installed — used for occasional data inspection only, not primary workflow

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

**UV does not load `.env` files automatically.** Use `uv run --env-file .env your_script.py` to load them explicitly. For scripts that need environment variables at import time (dlt pipelines, Claude API calls), use python-dotenv: `uv add python-dotenv`, then `from dotenv import load_dotenv; load_dotenv()` at the top of the script.

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

**Snowflake-native additions (Phase 3+):**
- dbt Projects on Snowflake (GA November 2025) — run dbt Core natively inside Snowflake, via a Git-connected Workspace + a deployed `DBT PROJECT` object. Explored in Phase 3 (currently unconfigured — requires a GitHub API integration and a Git-connected Workspace to populate). Deferred — will be weighed against Dagster OSS/Prefect/GitHub Actions when finalizing the Phase 5 orchestration choice.
- Snowflake Semantic Views (Standard SQL querying GA March 2026) — warehouse-native semantic layer, zero extra cost
- Snowflake Cortex Analyst — NL querying over semantic views, ~$5–15/month at hobby scale

**Estimated monthly cost: ~$60–75/month.** Snowflake ~$30–40; Cortex experiments ~$5–15; Claude Pro $20; Anthropic API (Phase 7+) ~$5–10; everything else free.

---

### Key Architectural Decisions

**Why dlt over Airbyte:** Airbyte is Docker-heavy, its free tier has been uncertain, and dlt teaches ingestion at code level rather than abstracting it behind a UI. Engineering-driven teams increasingly use dlt as their first choice.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow YAML is the OSI v1.0 reference implementation — learning it now means learning the emerging industry standard for semantic layers. Cube provides the API exposure layer that dbt Cloud would otherwise lock behind $100/month. The combination covers the full workflow at zero cost.

**Why Dagster OSS or Prefect over Dagster Cloud:** Dagster Cloud removed free credits from Solo and Starter plans May 1, 2026 — every asset materialization is now billed from zero at ~$0.035–0.040/credit with no grandfathering. Dagster OSS running locally as a Python process, or Prefect Cloud free Hobby tier (2 users, 5 workflows, 500 minutes serverless compute, no credit card required), covers the same learning goals.

**Why S3 + Iceberg + Snowflake Open Catalog over self-hosted Polaris or AWS Glue (decided June 2026):** Adding a bronze layer — raw data landing in S3 as Iceberg tables instead of being loaded directly into Snowflake — decouples storage from compute. Snowflake and DuckDB can both read the exact same physical files without separate load steps, extending the dbt-portability thesis (swap transformation engines, same SQL) to the storage layer (swap query engines, same data). Three catalog options were weighed:
- **Self-hosted Apache Polaris** — full control, fully open-source, but introduces a server only reachable from the Mac Mini. This breaks CI: GitHub Actions runners can't reach a catalog running on a laptop. Real problem starting at Phase 4, not a someday-Phase-8 concern.
- **AWS Glue** — zero-ops, matches the AWS dependency already accepted via S3, and the market-leading catalog by adoption. But it's proprietary, and doesn't extend the open-source-first preference (dbt Core, Iceberg, OSI) the way Polaris does.
- **Snowflake Open Catalog** — won. It's a managed hosting of the *actual* open-source Apache Polaris (same software, same principal/role model), free during the current billing period (0.5 credits/million requests after — negligible at hobby scale), and reachable by both local dev and CI since it's not self-hosted.

Self-hosted Polaris isn't rejected, just deferred — since Open Catalog runs the identical software, switching to self-hosting later (for the hands-on "I ran this myself" experience) costs little beyond re-registering a handful of tables and re-pointing engine configs. Whichever catalog is active, only one should ever write to a given S3 location — never register the same Iceberg table in two catalogs simultaneously.

**Why Evidence over Metabase:** Code-first, Git-native, designed for analytics engineers. Fits the everything-as-code philosophy of the stack. Cube Cloud free tier is dev/test only — if it changes, Cube Core runs as a local Node process at zero cost: `npm install -g @cubejs-backend/cli`.

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

**The gotcha (bit twice in Phase 3):** anything created through the Snowsight UI under your personal session is owned by whatever role that session defaults to. If that's `ACCOUNTADMIN` and `DBT_SERVICE_USER` runs as `SYSADMIN`, `SYSADMIN` has zero automatic access — Snowflake's role hierarchy doesn't flow downward to it. This surfaced as two different error messages for two different object types:
- **Table** (`RAW.GAMES`, loaded via the Catalog UI): `SQL compilation error: Object ... does not exist or not authorized` — Snowflake intentionally won't confirm whether an unauthorized role's target even exists.
- **Warehouse** (`COMPUTE_WH`, owned by `ACCOUNTADMIN`): `No active warehouse selected in the current session` — the dbt-snowflake connector passes `warehouse:` as a connection parameter (an implicit `USE WAREHOUSE`); if the role lacks `USAGE` on it, the connector fails to set it *silently* rather than erroring at connect time. The error only surfaces later, when a query actually needs compute (which is also why a view model succeeded — `CREATE VIEW` is metadata-only — while table models failed immediately after).

**Fix, either case:** grant the missing privilege explicitly, run as the object's owning role:
```sql
GRANT SELECT ON TABLE RAYS_ANALYTICS.RAW.GAMES TO ROLE SYSADMIN;
GRANT USAGE, OPERATE ON WAREHOUSE COMPUTE_WH TO ROLE SYSADMIN;
```
Better long-term fix: switch the Snowsight role selector to `SYSADMIN` *before* doing any manual UI work (loading data, creating warehouses), so objects are owned by the right role from creation instead of needing retroactive grants.

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
      account: <account_identifier>         # regional format: locator.region.aws
      user: DBT_SERVICE_USER
      private_key_path: ~/.ssh/dbt_service_user_rsa_key_p8.pem
      role: SYSADMIN
      database: RAYS_ANALYTICS
      warehouse: COMPUTE_WH
      schema: DEV
      threads: 4
    dev_duck:
      type: duckdb
      path: "{{ env_var('DUCKDB_PATH', 'dev.duckdb') }}"
      threads: 4
```

---

### Project Structure

```
~/projects/rays-analytics/          ← project root, Python scripts, git repo
  .venv/                            ← virtual environment (repo root, NOT in rays_analytics/)
  pyproject.toml                    ← project dependencies
  uv.lock                           ← pinned transitive dependency versions
  load_mlb_data.py                  ← MLB Stats API loader
  dev.duckdb                        ← local DuckDB file (gitignored)
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
- **Raw table:** `RAYS_ANALYTICS.RAW.GAMES` in Snowflake — populated via a one-time manual CSV export/load from DuckDB (Phase 3 stopgap, run through Catalog → Database Explorer's load wizard). **This is not a real pipeline** — it exists only to unblock testing `dbt build` against Snowflake. Will be replaced entirely by the Phase 4 dlt pipeline.
- **Rays team ID:** 139
- **Seasons loaded:** 2022, 2023, 2024 (486 games)
- **Star schema:** stg_games → dim_teams, dim_venues, fct_games
- **44 tests** — not_null, unique, accepted_values, relationships

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

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every PR to main.

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

**Dual-job architecture:** CI now runs two jobs. DuckDB runs on every PR (fast, free, catches structural errors — but SQL dialect differences mean DuckDB passing doesn't guarantee Snowflake passing). Snowflake only runs on merge to `main`, generating a `profiles.yml` dynamically using the service user's private key from a GitHub Secret — the key is written to a temp file during the run and referenced by path in the generated profile. Workload Identity Federation (Snowflake's preferred newer auth method) was researched and ruled out — unsupported in dbt-snowflake as of June 2026 — so key-pair auth is the deliberate, correct choice here, not a fallback.

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
- GitHub Actions CI updated — dual-job architecture: DuckDB job runs on every PR (fast, free, structural validation), Snowflake job runs only on merge to `main` (real warehouse validation) using dynamically-generated key-pair profile ✅
- GitHub Secrets configured — `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_PRIVATE_KEY`; `SNOWFLAKE_USER` hardcoded (not sensitive) ✅
- Workload Identity Federation researched and ruled out — unsupported in dbt-snowflake as of June 2026; key-pair auth confirmed correct ✅
- `RAYS_ANALYTICS.RAW.GAMES` populated via one-time manual CSV stopgap (486 games) ✅
- Full `dbt build` passing against real Snowflake data — models and all 44 tests ✅
- Snowflake privilege/RBAC gotcha hit and resolved twice (table + warehouse ownership) — see Role Hierarchy notes ✅
- Query Profile explored on a compiled model ✅
- dbt Projects on Snowflake explored (found unconfigured; deliberately deferred to Phase 5 decision) ✅

**Skills locked in:** Snowflake architecture, cost monitoring, key-pair authentication, account identifier formats, dbt-snowflake adapter setup, dual-environment CI design (DuckDB/Snowflake split), GitHub Secrets-based service auth in CI, Snowflake RBAC hierarchy and privilege troubleshooting, reading a Query Profile (Statistics pane, partition pruning, why a view vs. table model behaves differently), Snowsight navigation literacy, recognizing when a throwaway stopgap is the right scope vs. pulling a future phase forward prematurely.

---

#### Phase 4 — Ingestion (~2 weeks)

**⚠️ Before starting:** revisit whether dlt + GitHub Actions are still the right ingestion/orchestration tools for this project — not yet fully convinced. Worth comparing against Snowflake's native **Openflow** (built on Apache NiFi, lives under the new Ingestion nav category) while reconsidering. This is a deliberate pause, not a default — don't start building until this is resolved.

**Goal:** Replace `load_mlb_data.py` with a proper dlt pipeline; add Statcast data via pybaseball; configure Snowflake as destination; build staging models over dlt raw output; implement incremental loading.

**Key notes:**
- Install dlt and Marimo with `uv add dlt marimo`
- dlt lands raw data in the RAW schema; add dbt sources YAML pointing at dlt's raw tables
- Incremental loading requires a cursor column — understand dlt state management
- Update season list to include 2025 and 2026; update `accepted_values` tests accordingly
- Deliberately introduce a schema change and observe how dlt and dbt source freshness tests respond
- Loading data into `RAYS_ANALYTICS.RAW.GAMES` is the first task of this phase — this replaces the manual CSV stopgap from Phase 3 entirely
- **Bronze layer architecture (decided June 2026, supersedes the earlier dual-destination dlt plan):** dlt writes once — landing raw data as Iceberg tables in S3, cataloged via Snowflake Open Catalog. Snowflake and DuckDB both *read* from that same bronze location as two separate engines; dlt no longer needs to maintain two load destinations. One-time setup: an `ORGADMIN`-created Open Catalog account, an S3 bucket in the same region as Snowflake (us-east-2), and IAM credentials scoped to that bucket.
- **Cadence, simplified by the bronze layer:** there's now only one write cadence to think about — when fresh data lands in S3 (scheduled via cron/GitHub Actions for the "production" cadence). Snowflake and DuckDB both read live from whatever's currently in the bronze layer at query time; DuckDB no longer needs its own separate on-demand load step, since reading is reading regardless of which engine does it.
- **Single-writer discipline:** only Open Catalog should ever write to the bronze S3 location. Never register the same Iceberg table in two catalogs at once — they don't share transaction state and will corrupt each other's metadata pointers.
- As part of this phase, also flip `profiles.yml`'s default local target from `dev` (Snowflake) to `dev_duck`, and confirm a full `dbt build` still passes cleanly against DuckDB before building anything new on top of it — carried over from Phase 3 wrap-up, not yet done.

**Skills locked in:** Python-based ingestion, raw/staging layer pattern, incremental loading, schema drift handling, source freshness testing, exploratory data analysis with Marimo, Iceberg table format and REST catalog mechanics, S3/IAM setup, storage-layer portability (multiple engines reading one physical dataset).

---

#### Phase 5 — Orchestration and Observability (~2 weeks)

**Goal:** Wrap dbt and dlt in Dagster assets or Prefect flows; define explicit dependency between loader and build; schedule the full pipeline; wire up Elementary and Slack alerts; deliberately break something.

**Key notes:**
- Dagster Cloud removed free credits May 1, 2026 — use Dagster OSS or Prefect Cloud free Hobby tier
- Elementary: run `edr report` after dbt builds; configure Slack alerts for failures
- Add dbt source freshness checks — stale dlt syncs surface as pipeline failures
- **Also weigh dbt Projects on Snowflake** as a fourth option alongside Dagster OSS/Prefect/GitHub Actions when making the final call — it was explored but deliberately not adopted in Phase 3. Native Git-connected dbt execution inside Snowflake could plausibly replace some combination of the CI Snowflake job and a scheduler, worth a real comparison rather than defaulting to it just because it's already partly explored.

**Skills locked in:** Asset-based orchestration, scheduled runs, dependency management, failure alerting, data observability, incident response.

---

#### Phase 6 — Semantic Layer (~2 weeks)

**Goal:** Define MetricFlow semantic models and metrics; create Snowflake Semantic Views on top of the mart layer; expose metrics via Cube; build and deploy an Evidence report.

**Key notes:**
- MetricFlow YAML is the OSI v1.0 reference implementation
- Cube Cloud free tier is for dev/test only; Cube Core runs locally: `npm install -g @cubejs-backend/cli`
- Connect Evidence to Cube's API, not directly to Snowflake
- Deploy Evidence report to Vercel free tier or GitHub Pages

**Skills locked in:** MetricFlow YAML, Snowflake Semantic Views, Cube as API-first semantic layer, BI consumption of governed metrics, full author-to-consume workflow.

---

#### Phase 7 — AI Layer (~$5–10/month API, ~2 weeks)

**Goal:** Query the semantic layer with natural language via Snowflake Cortex Analyst and Claude API; explore MCP for direct semantic layer access from Claude Code.

**Key notes:**
- Set a $10/month spend cap in Anthropic account settings before writing any API calls
- Compare Snowflake Cortex Analyst vs Claude API over Cube
- Cube has an MCP server — query the semantic layer directly from Claude Code terminal

**Skills locked in:** AI-over-data patterns, text-to-metric vs text-to-SQL, semantic layer as AI context, API spend management, MCP orchestration.

---

#### Phase 8 — CI/CD and Portfolio (~1 week)

**Goal:** Implement slim CI with state-based selection; add MetricFlow validation; write a comprehensive README; record a walkthrough of the full stack end-to-end.

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

**Next actions:**
1. Confirm `ALTER USER <username> SET DEFAULT_ROLE = SYSADMIN;` was actually run (discussed, not explicitly confirmed executed)
2. Flip local `profiles.yml` default target to `dev_duck`; confirm `dbt build` still passes clean against DuckDB (Phase 3 wrap-up, carried into Phase 4 prep)
3. Before writing any Phase 4 code: resolve the dlt/GitHub Actions tooling re-evaluation (compare against Snowflake Openflow, among others)
4. Once tooling is settled, begin Phase 4 with the bronze layer design already decided (S3 + Iceberg, cataloged via Snowflake Open Catalog)

**Decisions made this session not captured elsewhere:**
- No new phase number for "DuckDB-first dev workflow" — it's a discipline applied within Phase 4, not a separate phase
- Two-role default for day-to-day Snowsight use (`SYSADMIN` default, `ACCOUNTADMIN` for account-level only) — full four-role rotation judged as enterprise ceremony not worth it solo
- Snowflake Optima Metadata (automatic pruning metadata for high-frequency query patterns) noted as existing but not relevant at current hobby-project query volume