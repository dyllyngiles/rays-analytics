# Rays Analytics — Project Instructions

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

My name is Dyllyn Giles. I'm based in Versailles, Kentucky. I work as an analytics engineer with existing dbt experience but no modern cloud warehouse experience. My goal is to build a complete, portfolio-ready modern ELT stack for learning and career development. My personal knowledge system is a pencil and notebook. I prefer to understand what I'm doing rather than just following commands.

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

**`profiles.yml` lives at `~/.dbt/profiles.yml`** — never committed to the repo. Local config points to `dev.duckdb` at repo root.

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

**dbt Core vs dbt Fusion:** dbt Labs launched dbt Fusion in May 2025 — a Rust-based rewrite of dbt Core, GA for Snowflake on the dbt platform. It is licensed under ELv2 (non-compete clause, not Apache 2.0). dbt Core remains the right choice for this self-hosted stack: open source, fully supported, no vendor lock-in. Fusion is primarily relevant to dbt platform (Cloud) users. Worth monitoring as it matures.

**Snowflake-native dbt:** GA November 2025. No additional licensing cost — pay only warehouse credits. Worth exploring alongside the local dbt workflow in Phase 3.

**Snowflake Semantic Views:** Standard SQL querying GA March 2026. Zero extra cost, zero infrastructure overhead. Snowflake-only, but this stack is Snowflake-only in production.

**dbt/Fivetran merger:** Announced October 2025, expected to close mid–late 2026. dbt Core remains Apache 2.0 open source. No impact on this stack.

---

### Tools Not in the Stack

| Tool | Reason excluded |
|---|---|
| Airbyte | Docker-heavy; free tier uncertain; dlt teaches more |
| Dagster Cloud | Free credits removed May 2026; per-asset billing from zero |
| dbt Cloud | $100/seat/month for Semantic Layer API access |
| dbt Fusion | ELv2 license (not Apache 2.0); primarily for dbt platform users |
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

### Project Structure

```
~/projects/rays-analytics/          ← project root, Python scripts, git repo
  .venv/                            ← virtual environment (repo root, NOT in rays_analytics/)
  pyproject.toml                    ← project dependencies
  uv.lock                           ← pinned transitive dependency versions
  load_mlb_data.py                  ← MLB Stats API loader
  dev.duckdb                        ← local DuckDB file (gitignored)
  publish_docs.sh                   ← publishes dbt docs to GitHub Pages
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
- **Raw table:** `raw.games` in DuckDB
- **Rays team ID:** 139
- **Seasons loaded:** 2022, 2023, 2024 (486 games)
- **Star schema:** stg_games → dim_teams, dim_venues, fct_games
- **44 tests passing** — not_null, unique, accepted_values, relationships

**Known deprecation warning:** CI logs show `MissingArgumentsPropertyInGenericTestDeprecation` on the `relationships` test in `models/marts/schema.yml`. Arguments to generic tests should be nested under an `arguments` property. Low priority — address in Phase 3 when porting models to Snowflake.

---

### Workflow Conventions

- Always `cd rays_analytics` for dbt commands
- Activate venv and navigate at session start:
  ```bash
  cd ~/projects/rays-analytics
  source .venv/bin/activate    # activates from repo root
  cd rays_analytics             # then move into dbt project for dbt commands
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

**Actions pinning:** All actions are pinned to exact commit hashes, not floating version tags. The March 2025 tj-actions/changed-files compromise — which leaked secrets from thousands of repositories via a hijacked tag — is the canonical reason why. A floating tag like `@v6` can be silently repointed to malicious code. Current pinned hashes:
- `actions/checkout` v6.0.2 → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `astral-sh/setup-uv` v8.1.0 → `08807647e7069bb48b6ef5acd8ec9567f424441b`

**Dependency installation:** `uv sync --locked` — verifies `uv.lock` is consistent with `pyproject.toml` and fails if they've drifted. See Key Environment Decisions for the `--locked` vs `--frozen` distinction.

**Dependency auditing:** `uv audit` runs as a CI step. Built into uv 0.10.12+, no additional install required. Checks all locked dependencies against the OSV vulnerability database and returns a non-zero exit code on findings, which fails the CI step.

**UV version:** Pinned to `0.11.16` to match local version exactly.

**Venv location:** Created at repo root (no `working-directory` on the install step) to match local layout and be accessible to both the loader and dbt.

**Loader step:** Activates `.venv/bin/activate` from repo root, then runs `load_mlb_data.py`. Runs at repo root by default, which is where the script lives.

**dbt build step:** Uses `../.venv/bin/activate` (one level up from `rays_analytics/`) to reach the repo root venv. `working-directory: rays_analytics`.

**DuckDB path in CI:** `/home/runner/work/rays-analytics/rays-analytics/dev.duckdb` — set via `DUCKDB_PATH` env var on the loader step.

**Profiles.yml in CI:** Generated dynamically — CI has no `~/.dbt/` directory. Step creates it with `mkdir -p ~/.dbt` and writes the file.

**Phase 3 CI transition:** When porting to Snowflake, the dynamic profiles.yml generation step changes significantly. Snowflake password authentication is deprecated for new accounts (see Phase 3 notes). The dbt service account must use key-pair authentication. The private key is stored as a GitHub Secret, written to a temp file during the CI run, and referenced by path in the generated profile.

---

### Learning Roadmap

#### Phase 1 — Foundation ✅ COMPLETE

**Skills locked in:** dbt project structure, staging/mart layering, testing discipline, documentation habits, columnar warehouse thinking, star schema dimensional modeling, feature branch git workflow.

---

#### Phase 2 — Version Control 🔄 IN PROGRESS

**Completed:**
- `.gitignore`, `profiles.yml` kept outside repo, project pushed to public GitHub
- Feature branch workflow established
- CI workflow (`ci.yml`) fully passing — 48/48 tests green ✅
- `load_mlb_data.py` updated — relative DuckDB path via `os.getenv`, connection scoping, error handling, timeout ✅
- `pyproject.toml` and `uv.lock` added — CI uses `uv sync --locked` ✅
- dbt docs published to GitHub Pages ✅
- Pin `actions/checkout` to v6.0.2 hash ✅
- Swap `uv sync --frozen` → `uv sync --locked` in `ci.yml` ✅
- Add `uv audit` step to `ci.yml` ✅

**Remaining:**
- Set branch protection rules — PRs must pass CI before merging
- Write README — project overview, data source, modeling decisions, CI explanation

**Skills locked in:** Git-based workflow, CI pipeline authoring, PR-driven development, branch protection, secrets management discipline, CI debugging from logs, dependency auditing.

---

#### Phase 3 — Real Warehouse (~$30–40/month, ~2 weeks)

**Goal:** Swap the dbt adapter from DuckDB to Snowflake, port all models, configure dev/prod environments, and establish cost controls.

**Key tasks:**
- Create Snowflake trial account; understand object hierarchy (account → database → schema → table)
- Set up Resource Monitor immediately — cap $20/month, alert at 75%
- Configure warehouse with 60-second auto-suspend and auto-resume
- Set up key-pair authentication for dbt service account (see authentication note below)
- Install dbt-snowflake v1.11.x (`uv add dbt-snowflake`)
- Update `profiles.yml` locally to point at Snowflake with key-pair auth
- Port models to Snowflake; create DEV and PROD schemas
- Fix `relationships` test deprecation warning (nest arguments under `arguments` property)
- Update GitHub Actions CI — swap DuckDB profile generation for Snowflake key-pair profile
- Open Query Profile on a compiled model — build the habit of understanding what Snowflake executes
- Explore dbt Projects on Snowflake Workspaces; compare to local dbt workflow

**⚠ Authentication note — read before creating your Snowflake account:**
Snowflake is deprecating single-factor password authentication in a phased rollout through 2026. For accounts created now: newly created human users must use MFA (enforced May–July 2026); service users must use key-pair, OAuth, or PAT — password auth is blocked (enforced August–October 2026). Practically: do not configure `password:` in `profiles.yml` or CI for the dbt service account. Set up key-pair authentication from day one. This requires generating an RSA key pair, registering the public key with the Snowflake user, and storing the private key path (locally) or private key content (as a GitHub Secret in CI).

**⚠ dbt-snowflake version note:**
Snowflake increased default column size for string/binary types in May 2026. dbt-snowflake versions below v1.10.6 fail to build incremental models using `on_schema_change: sync_all_columns` when string columns don't specify a width. Current compatible version is 1.11.4. Install current, not minimum.

**Skills locked in:** Snowflake architecture, cost monitoring, dev/prod separation, query profiling, resource management, key-pair authentication, Snowflake-native dbt.

---

#### Phase 4 — Ingestion (~2 weeks)

**Goal:** Replace `load_mlb_data.py` with a proper dlt pipeline; add Statcast data via pybaseball; configure Snowflake as destination; build staging models over dlt raw output; implement incremental loading.

**Key notes:**
- Install dlt and Marimo with `uv add dlt marimo`
- dlt lands raw data in the RAW schema; add dbt sources YAML pointing at dlt's raw tables
- Incremental loading requires a cursor column — understand dlt state management
- Update season list to include 2025 and 2026; update `accepted_values` tests accordingly
- Deliberately introduce a schema change and observe how dlt and dbt source freshness tests respond

**Skills locked in:** Python-based ingestion, raw/staging layer pattern, incremental loading, schema drift handling, source freshness testing, exploratory data analysis with Marimo.

---

#### Phase 5 — Orchestration and Observability (~2 weeks)

**Goal:** Wrap dbt and dlt in Dagster assets or Prefect flows; define explicit dependency between loader and build; schedule the full pipeline; wire up Elementary and Slack alerts; deliberately break something.

**Key notes:**
- Dagster Cloud removed free credits May 1, 2026 — use Dagster OSS (local Python process) or Prefect Cloud free Hobby tier (2 users, 5 workflows, 500 serverless compute minutes, no credit card required)
- Elementary: run `edr report` after dbt builds; configure Slack alerts for failures
- Add dbt source freshness checks — stale dlt syncs surface as pipeline failures

**Skills locked in:** Asset-based orchestration, scheduled runs, dependency management, failure alerting, data observability, incident response.

---

#### Phase 6 — Semantic Layer (~2 weeks)

**Goal:** Define MetricFlow semantic models and metrics; create Snowflake Semantic Views on top of the mart layer; expose metrics via Cube; build and deploy an Evidence report.

**Key notes:**
- MetricFlow YAML is the OSI v1.0 reference implementation — learning the spec now, not just the tool
- Cube Cloud free tier is for dev/test only; Cube Core runs locally as a Node process: `npm install -g @cubejs-backend/cli`
- Connect Evidence to Cube's API, not directly to Snowflake — this is the governed pattern
- Deploy Evidence report to Vercel free tier or GitHub Pages

**Skills locked in:** MetricFlow YAML, Snowflake Semantic Views, Cube as API-first semantic layer, BI consumption of governed metrics, full author-to-consume workflow.

---

#### Phase 7 — AI Layer (~$5–10/month API, ~2 weeks)

**Goal:** Query the semantic layer with natural language via Snowflake Cortex Analyst and Claude API; explore MCP for direct semantic layer access from Claude Code.

**Key notes:**
- Set a $10/month spend cap in Anthropic account settings before writing any API calls
- Compare Snowflake Cortex Analyst (warehouse-native, zero portability) vs Claude API over Cube (portable, framework-agnostic)
- Cube has an MCP server — query the semantic layer directly from Claude Code terminal without writing Python

**Skills locked in:** AI-over-data patterns, text-to-metric vs text-to-SQL, semantic layer as AI context, API spend management, MCP orchestration.

---

#### Phase 8 — CI/CD and Portfolio (~1 week)

**Goal:** Implement slim CI with state-based selection; add MetricFlow validation; write a comprehensive README; record a walkthrough of the full stack end-to-end.

**Key notes:**
- Slim CI: `dbt build --select state:modified+` on PRs only — requires a manifest artifact from the last prod run
- Create a dedicated CI Snowflake warehouse (X-Small, 60-second auto-suspend) for isolated cost tracking separate from dev/prod

**Skills locked in:** Slim CI, multi-environment warehouse management, metric validation in CI, portfolio documentation.

---

### Session Handoff

*Update this at the end of every working session — not just at phase boundaries. Paste the full instructions document plus this section at the start of a new chat to resume without a verbal debrief.*

**Last session:**
- Hardened CI: pinned `actions/checkout` to v6.0.2 hash, swapped `--frozen` → `--locked`, added `uv audit` step — merged via PR #6

**Active branch:** `main` (all changes merged, branch clean)

**Next actions:**
1. Set branch protection rules in GitHub — PRs must pass CI before merging
2. Write README — project overview, data source, modeling decisions, CI explanation

**Decisions made this session not captured elsewhere:**
- `uv audit` is the dependency scanning approach — built into uv, no extra install, replaces the pip-audit/Dependabot option that was previously listed
- Use Claude Code for implementation work; use this chat interface for research, planning, and documentation