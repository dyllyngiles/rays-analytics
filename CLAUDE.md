# Rays Analytics — Project Instructions

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

My name is Dyllyn Giles. I'm based in Lexington, Kentucky. I work in analyticd with some dbt experience but no modern cloud warehouse experience. My goal is to build a complete, portfolio-ready modern ELT stack for learning and career development. My personal knowledge system is a pencil and notebook. I prefer to understand what I'm doing rather than just following commands.

---

### My Machine

- M4 Mac Mini, 16GB RAM
- macOS, Apple Silicon (aarch64)

---

### Local Environment

- Homebrew (package manager)
- UV 0.11.16 (Python package and environment manager — replaces both pip and pyenv)
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
- dbt Projects on Snowflake (GA November 2025) — run dbt Core natively inside Snowflake Workspaces, no external infrastructure
- Snowflake Semantic Views (Standard SQL querying GA March 2026) — warehouse-native semantic layer, zero extra cost
- Snowflake Cortex Analyst — NL querying over semantic views, ~$5–15/month at hobby scale

**Estimated monthly cost: ~$60–75/month.** Snowflake ~$30–40; Cortex experiments ~$5–15; Claude Pro $20; Anthropic API (Phase 7+) ~$5–10; everything else free.

---

### Key Architectural Decisions

**Why dlt over Airbyte:** Airbyte is Docker-heavy, its free tier has been uncertain, and dlt teaches ingestion at code level rather than abstracting it behind a UI. Engineering-driven teams increasingly use dlt as their first choice.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow YAML is the OSI v1.0 reference implementation — learning it now means learning the emerging industry standard for semantic layers. Cube provides the API exposure layer that dbt Cloud would otherwise lock behind $100/month. The combination covers the full workflow at zero cost.

**Why Dagster OSS or Prefect over Dagster Cloud:** Dagster Cloud removed free credits from Solo and Starter plans May 1, 2026 — every asset materialization is now billed from zero at ~$0.035–0.040/credit with no grandfathering. Dagster OSS running locally as a Python process, or Prefect Cloud free Hobby tier (2 users, 5 workflows, 500 minutes serverless compute, no credit card required), covers the same learning goals.

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

### Snowsight Navigation (as of June 2026)

Snowsight was significantly reorganized. Key locations:

- **SQL editor (Workspaces):** Projects — Worksheets renamed to Workspaces as of April 2026
- **Warehouses:** Admin → Compute
- **Resource Monitors:** Admin → Cost Management
- **Legacy Worksheets removed:** June 22, 2026

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
- **Raw table:** `RAYS_ANALYTICS.RAW.GAMES` in Snowflake (not yet loaded — deferred to Phase 4)
- **Rays team ID:** 139
- **Seasons loaded:** 2022, 2023, 2024 (486 games)
- **Star schema:** stg_games → dim_teams, dim_venues, fct_games
- **44 tests** — not_null, unique, accepted_values, relationships

**Known deprecation warning:** `MissingArgumentsPropertyInGenericTestDeprecation` on the `relationships` test in `models/marts/schema.yml`. Arguments to generic tests should be nested under an `arguments` property. To be fixed as remaining Phase 3 work.

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

---

### CI Architecture Notes

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every PR to main.

**Actions pinning:** All actions are pinned to exact commit hashes, not floating version tags. The March 2025 tj-actions/changed-files compromise — which leaked secrets from thousands of repositories via a hijacked tag — is the canonical reason why. Current pinned hashes:
- `actions/checkout` v6.0.2 → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `astral-sh/setup-uv` v8.1.0 → `08807647e7069bb48b6ef5acd8ec9567f424441b`

**Dependency installation:** `uv sync --locked` — verifies `uv.lock` is consistent with `pyproject.toml` and fails if they've drifted.

**Dependency auditing:** `uv audit` runs as a CI step. Built into uv 0.10.12+, no additional install required.

**UV version:** Pinned to `0.11.16` to match local version exactly.

**Phase 3 CI transition:** CI currently runs against DuckDB. Needs to be updated to generate a Snowflake `profiles.yml` dynamically using the service user private key stored as a GitHub Secret. The private key content (PKCS#8 format) goes in as a secret, gets written to a temp file during the CI run, and is referenced by path in the generated profile.

---

### Learning Roadmap

#### Phase 1 — Foundation ✅ COMPLETE

**Skills locked in:** dbt project structure, staging/mart layering, testing discipline, documentation habits, columnar warehouse thinking, star schema dimensional modeling, feature branch git workflow.

---

#### Phase 2 — Version Control ✅ COMPLETE

**Skills locked in:** Git-based workflow, CI pipeline authoring, PR-driven development, branch protection, secrets management discipline, CI debugging from logs, dependency auditing.

---

#### Phase 3 — Real Warehouse 🔄 IN PROGRESS

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

**Remaining:**
- Fix `relationships` test deprecation warning in `models/marts/schema.yml`
- Update GitHub Actions CI — swap DuckDB profile generation for Snowflake key-pair profile
- Store private key as GitHub Secret
- Open Query Profile on a compiled model
- Explore dbt Projects on Snowflake Workspaces
- Data loading deferred to Phase 4 — `dbt build` will not fully pass until RAW.GAMES is populated

**Skills locked in so far:** Snowflake architecture, cost monitoring, key-pair authentication, account identifier formats, dbt-snowflake adapter setup.

---

#### Phase 4 — Ingestion (~2 weeks)

**Goal:** Replace `load_mlb_data.py` with a proper dlt pipeline; add Statcast data via pybaseball; configure Snowflake as destination; build staging models over dlt raw output; implement incremental loading.

**Key notes:**
- Install dlt and Marimo with `uv add dlt marimo`
- dlt lands raw data in the RAW schema; add dbt sources YAML pointing at dlt's raw tables
- Incremental loading requires a cursor column — understand dlt state management
- Update season list to include 2025 and 2026; update `accepted_values` tests accordingly
- Deliberately introduce a schema change and observe how dlt and dbt source freshness tests respond
- Loading data into `RAYS_ANALYTICS.RAW.GAMES` is the first task of this phase

**Skills locked in:** Python-based ingestion, raw/staging layer pattern, incremental loading, schema drift handling, source freshness testing, exploratory data analysis with Marimo.

---

#### Phase 5 — Orchestration and Observability (~2 weeks)

**Goal:** Wrap dbt and dlt in Dagster assets or Prefect flows; define explicit dependency between loader and build; schedule the full pipeline; wire up Elementary and Slack alerts; deliberately break something.

**Key notes:**
- Dagster Cloud removed free credits May 1, 2026 — use Dagster OSS or Prefect Cloud free Hobby tier
- Elementary: run `edr report` after dbt builds; configure Slack alerts for failures
- Add dbt source freshness checks — stale dlt syncs surface as pipeline failures

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
- Created Snowflake trial account — Standard edition, AWS us-east-2
- Configured Resource Monitor, warehouse, database, schemas
- Created DBT_SERVICE_USER with TYPE = SERVICE and key-pair auth
- Installed dbt-snowflake v1.11.4, updated profiles.yml
- Worked through account identifier issues — URL slug differs from actual identifier; use `SELECT SYSTEM$ALLOWLIST()` to find the correct regional format
- PKCS#8 key format required — standard `openssl genrsa` output (PKCS#1) fails with JWT error
- `dbt debug` passing; `dbt build` fails only because RAW.GAMES does not exist yet — expected, data loading deferred to Phase 4
- Snowsight UI reorganized — Worksheets is now Workspaces under Projects

**Active branch:** `main` (no feature branch open)

**Next actions:**
1. Open a feature branch
2. Fix `relationships` deprecation warning in `models/marts/schema.yml`
3. Update GitHub Actions CI — dynamic profiles.yml with key-pair auth, private key as GitHub Secret
4. Commit updated CLAUDE.md

**Decisions made this session not captured elsewhere:**
- Snowflake CoCo (formerly Cortex Code) announced at Summit — Snowflake's AI coding agent, not relevant to this stack at this phase
- AWS us-east-2 chosen — lowest on-demand credit cost, most common in job descriptions
- Regionless account identifier format did not work with dbt; regional format required
- Service user TYPE = SERVICE set correctly from day one per Snowflake auth deprecation rollout