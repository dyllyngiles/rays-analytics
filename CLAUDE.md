# Rays Analytics — Project Instructions

---

### Doc Maintenance (check every session that edits this file)

Claude Code has a 40k-character limit on this file. Run `wc -c CLAUDE.md` before considering any edit to this file done — not just after a large pass. Reasoning belongs in CHANGELOG.md, not here: cap Key Architectural Decisions bullets at one sentence of decision + one clause of why, and when a decision reverses another, delete the superseded reasoning from CLAUDE.md entirely (confirm CHANGELOG.md has the full "we tried X, moved to Y" history first). If `wc -c` comes back over 40k, compress before ending the session — don't leave it over the limit for the next session to discover.

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

I started this project with dbt and BI experience but no hands-on modern cloud warehouse experience — this project is where that's been built. Goal: a complete, portfolio-ready modern ELT stack for learning and career development. I prefer to understand what I'm doing rather than just following commands.

**Why I'm actually doing this project:** Curiosity and enjoyment. Job marketability is real and welcome but not the filter for what's worth exploring — don't gate discussing/prototyping an idea behind "does this earn its place." That scrutiny is for what becomes permanent, maintained stack infrastructure. Default to following interesting tangents.

That said, I still want honest pushback when something is actually unsound, outdated, or solving a problem that doesn't exist — different from ROI-gating, regardless of how fun the idea sounded. Real constraint I care about: not spending a lot of money. Flag other practical parameters as they come up — maintenance burden, new credentials meaning new security surface, the 16GB RAM ceiling.

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

**Docker is not currently part of the stack (reversed back, August 2026).** It briefly ran via Docker Compose on a VPS for self-hosted Dagster; that whole approach was abandoned (see Phase 5) and the VPS decommissioned. The Mac Mini runs no containers, and nothing else currently needs Docker.

**`profiles.yml` lives at `~/.dbt/profiles.yml`** — never committed. Points to Snowflake DEV schema. `dev_duck` removed from `ci.yml` (September 2026); local `profiles.yml`/Makefile still carry it as an ad hoc scratchpad target.

**DuckDB path is always relative** (`dev.duckdb`) from repo root, never hardcoded absolute. `DUCKDB_PATH` overrides it in CI.

**UV does not load `.env` files automatically.** Use `uv run --env-file .env <command>` to load them explicitly — works for any command in the venv (e.g. `uv run --env-file .env dbt build`). For scripts needing env vars at import time, use python-dotenv: `from dotenv import load_dotenv; load_dotenv()`.

---

### The Stack

| Layer | Tool | Status | Notes |
|---|---|---|---|
| Ingestion | dlt | **Running** | Python library, no Docker |
| Bronze storage | Amazon S3 | Bonus track, not started | Same region as Snowflake (us-east-2); raw Iceberg tables, engine-agnostic |
| Iceberg catalog | Snowflake Open Catalog (managed Apache Polaris) | Bonus track, not started | Free during current billing period; same software as self-hosted Polaris if revisited |
| Warehouse (local dev) | DuckDB | Demoted, ad hoc scratchpad only | Dropped as a dbt build target August 2026 — CLI/Marimo only now. `ci.yml` is Snowflake-only as of September 2026 |
| Warehouse (cloud) | Snowflake | **Running** | ~$35–55/month, X-Small, 60-sec auto-suspend |
| Transformation | dbt Core + dbt-snowflake | **Running** | Snowflake-only build target |
| Semantic layer | MetricFlow + Cube Core/Cloud free | Planned, Phase 6 | Cube's necessity under reconsideration — see Key Architectural Decisions |
| Orchestration | GitHub Actions | **Running** | PR/merge gate (`ci.yml`) plus daily production scheduling (`games_pipeline.yml`). Reversed from self-hosted Dagster OSS on a VPS — see Phase 5 |
| Observability | TBD | Decided, not yet implemented | Was planned as Dagster asset checks; needs a new plan now that Dagster is off the table. Elementary still optional |
| BI | Evidence | Planned, Phase 6 | Code-first, Git-native — not yet installed or configured |
| Version control + CI | GitHub + GitHub Actions | **Running** | |
| Notebooks | Marimo | **Running** | Added to `pyproject.toml` August 2026; ad hoc DuckDB scratchpad use case |
| AI development | Claude Pro + Claude Code + Anthropic API | Planned, Phase 7+ | Claude Code itself is in active use; the Phase 7 AI-layer integration hasn't started |

### Scope Tracks (added June 2026)

Roadmap is split into two tracks so the application timeline isn't gated by platform-depth exploration that's fun but not required.

**Core path (apply-ready, collapsed timeline):** Phase 4 slimmed (dlt → Snowflake `RAW` directly, no bronze/Iceberg); Phase 6 elevated (MetricFlow + Snowflake Semantic Views are core, not optional); Phase 8 pulled forward (README + walkthrough); new low-effort public self-serve demo via Evidence's Universal SQL (DuckDB-WASM) over Parquet on GitHub Pages, zero backend/cost. Phase 5 orchestration history: see Phase 5 below.

**Bonus / platform-depth track (curiosity-driven, no deadline):** Bronze layer (S3 + Iceberg + Snowflake Open Catalog, future self-hosted Polaris/Lakekeeper); deep Snowflake exploration (Time Travel, Zero-Copy Cloning, Cortex, Marketplace, Streamlit); Phase 7 AI/MCP layer incl. a MotherDuck Dives sandbox; self-serve BI tool decision (Lightdash vs. Metabase).

---

**Snowflake-native additions (Phase 3+):**
- dbt Projects on Snowflake (GA November 2025) — native dbt Core via a Git-connected Workspace + `DBT PROJECT` object. Explored in Phase 3, unconfigured — bonus-track curiosity only.
- Snowflake Semantic Views (GA March 2026) — warehouse-native semantic layer, zero extra cost
- Snowflake Cortex Analyst — NL querying over semantic views, ~$5–15/month at hobby scale

**Estimated monthly cost: ~$65–95/month** — Snowflake ~$35–55, Cortex ~$5–15, Claude Pro $20, Anthropic API (Phase 7+) ~$5–10, rest free. No VPS line item — see Phase 5.

---

### Key Architectural Decisions

Every bullet below is a one-line decision + reason. Full reasoning, alternatives considered, and reversal history for all of these: see CHANGELOG.md.

**Why dlt over Airbyte:** Airbyte is Docker-heavy with an uncertain free tier; dlt teaches ingestion at code level.

**Why dlt over Snowflake Openflow (June 2026):** MLB Stats API/pybaseball are bespoke sources outside Openflow's ~20 supported connectors, and Openflow needs infra that fights the RAM ceiling.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow is the OSI v1.0 reference implementation for semantic layers; Cube covers the API-exposure layer dbt Cloud locks behind $100/month.

**Cube's necessity reconsidered (June 2026):** Cube isn't itself a dashboard tool — now optional pending the Phase 6 BI-tool decision.

**Dagster OSS on a self-hosted DigitalOcean VPS, abandoned:** MLB Stats API blocks DigitalOcean's IP range at the CDN level — see Phase 5 below.

**Why S3 + Iceberg + Snowflake Open Catalog over self-hosted Polaris or AWS Glue (June 2026, bonus track):** Open Catalog is managed Polaris — free, CI-reachable, open-source-first.

**Why Evidence over Metabase:** Code-first, Git-native; Cube Core runs as a free local Node process if needed.

**Public self-serve demo (June 2026):** Evidence's Universal SQL (DuckDB-WASM) over Parquet on GitHub Pages — zero backend cost.

**Self-serve BI tool decision (June 2026, deferred to Phase 6):** Lightdash needs Docker; Metabase keeps metrics outside dbt. Not yet decided.

**dlt `games` resource — completed games only (June 2026):** filters to `Final`/`Completed Early` before yielding — a deliberate scope call, not a technical limitation.

**Why `games` doesn't use dlt's `incremental()` (June 2026):** the schedule endpoint has no true modified-since cursor, so full-season re-pull + `merge` on `game_pk` is used instead — won't hold once a higher-volume, real-cursor source is added.

**dlt pipeline destination is parameterized (June 2026):** `pipelines/mlb_games.py` takes `--destination duckdb|snowflake` (default `duckdb`) so DuckDB refreshes stay free while Snowflake spend is opt-in.

**DuckDB dropped as a dbt build target (decided August 2026):** dbt builds only against Snowflake now; DuckDB demoted to an ad hoc scratchpad — the multi-engine goal never paid for itself at this size. CI's response: see CI Architecture Notes.

**Delta Lake evaluated and rejected (decided August 2026):** see Tools Not in the Stack.

**dlt table ownership gotcha (hit June/July 2026):** dlt can't retrofit tracking columns onto a table it didn't create — drop and let dlt recreate it from a clean slate.

**`dim_teams`/`dim_venues` dedup — most-recent-name-wins (June 2026):** ranks rows per id by `game_date desc` to handle team/venue renames over time.

**Secrets consolidation — single `.env` (decided July 2026):** dlt and dbt both read one gitignored `.env` at repo root, replacing a separate `.dlt/secrets.toml`.

**Why 16GB Mac Mini is sufficient (reworded August 2026):** nothing in the current stack runs on Docker — the Dagster/VPS Docker Compose experiment was abandoned (see above) — so the RAM ceiling isn't a live constraint on any tool choice.

**Why key-pair for CI Snowflake auth (reversed July 2026):** the WIF prerequisite (`dbt-labs/dbt-adapters` PR #1316) was never merged — key-pair matches dlt, no asymmetry. See Snowflake CI Auth Notes below.

**dbt Core vs dbt Fusion vs dbt Core v2.0:** v2.0 (Fusion, Apache 2.0) is alpha; v1.11.x stays the daily driver until Phase 8.

**Snowflake-native dbt (GA Nov 2025) / Snowflake Semantic Views (GA Mar 2026):** both zero extra cost beyond warehouse credits, Semantic Views Snowflake-only (matches this stack's Snowflake-only posture).

**dbt/Fivetran merger / Prefect/Dagster acquisition (2026):** both stay Apache 2.0/self-hostable — no impact on stack choices, just vendor-risk framing to watch.

**Claude Code reads `.env` directly when generating config that references it (flagged August 2026):** confirmed while wiring Postgres credentials into the Compose stack. Explicitly instruct it not to touch `.env` per task; treat anything it read as exposed. Full narrative: see CHANGELOG.md.

---

### Tools Not in the Stack

| Tool | Reason excluded |
|---|---|
| Airbyte | Docker-heavy; free tier uncertain; dlt teaches more |
| Dagster Cloud | Free credits removed May 2026; per-asset billing from zero |
| dbt Cloud | $100/seat/month for Semantic Layer API access |
| dbt Fusion (distribution) | Proprietary extensions above Apache 2.0 runtime; v2.0 alpha not production-ready |
| Fivetran | Pricing restructured March 2025; per-connector costs increased 50–60% |
| Jupyter | Replaced by Marimo — git-friendly, no hidden state, saves as Python files |
| MotherDuck | Third portability target considered June 2026; deprioritized — work-related interest, not project-specific |
| AWS Glue | Considered for the Iceberg catalog; zero-ops but proprietary |
| Airflow | Common in AE postings but not required — concepts transfer from Dagster/Prefect |
| Delta Lake | Bronze-layer dedup alternative, considered Aug 2026; added complexity not worth it, lower job-market signal than the Iceberg bonus track |
| AWS-native orchestration hosting (EC2/ECS/RDS) | Considered Aug 2026; costlier/over-complex for a solo ~daily pipeline |
| Hetzner (VPS) | US region pricing (Ashburn/Hillsboro) runs ~2-3x EU rate as of Aug 2026 — most expensive option checked, not cheapest; don't re-default on EU-reputation cost assumptions |
| Mac Mini (VPS substitute) | Root cause: FileVault vs. auto-login conflicts with unattended reboot — no reliable SSH/network access pre-login without a human present |
| Dagster OSS on a self-hosted VPS | Built and deployed August 2026, then abandoned: MLB Stats API blocks DigitalOcean's IP range at the CDN level — see Phase 5, full history on `archive/phase-5-dagster-vps` |


*Docker itself is no longer in this table — see Key Environment Decisions (reversed August 2026).*

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
- **CI service user:** RAYS_ANALYTICS_CI_SERVICE — TYPE = SERVICE, SYSADMIN role, key-pair auth (reversed from WIF, July 2026). Key: `~/.ssh/ci_service_user_rsa_key_p8.pem` (PKCS#8) — see Snowflake CI Auth Notes below

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

### Snowflake CI Auth Notes

**Decision (reversed July 2026):** the Snowflake-on-merge CI job authenticates via key-pair, not WIF. The "PR merged May 20, 2026" claim was wrong — `dbt-labs/dbt-adapters` PR #1316 (Snowflake WIF support) is still open since September 2025, blocked on a maintainer requirement for integration-test infra (dbt-snowflake v1.12.0 milestone shows it 45% complete). Reversed to key-pair — dlt and dbt both use key-pair in CI now, no asymmetry.

**`RAYS_ANALYTICS_CI_SERVICE` setup, completed this session:**
- Authentication policy `WIF_GITHUB_ONLY` (in `RAYS_ANALYTICS.RAW`) stays attached and ACTIVE — `AUTHENTICATION_METHODS = [ALL]`, not restricted to WORKLOAD_IDENTITY, so key-pair auth is permitted under it. Left attached rather than removed: dormant, ready if WIF ships later.
- `RSA_PUBLIC_KEY` was null (WIF meant no key had ever been generated). New key-pair generated and registered:
```bash
openssl genrsa -out ci_service_rsa_key.pem 2048
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt \
  -in ci_service_rsa_key.pem -out ci_service_rsa_key_p8.pem
openssl rsa -in ci_service_rsa_key.pem -pubout -out ci_service_rsa_key.pub
```
Private key: `~/.ssh/ci_service_user_rsa_key_p8.pem` (chmod 600), separate from `DBT_SERVICE_USER`'s key. Verified via `dbt debug --target ci_test` — `ci_test` is a **kept, intentional** local target, not a one-time throwaway: `make dbt-debug-ci` depends on it as a repeatable pre-merge sanity check that CI auth still works before pushing to main. It stays in `~/.dbt/profiles.yml` deliberately. A fresh clone needs to add it manually (not checked in — see Current `profiles.yml` structure below for why credentials stay out of the repo):

```yaml
    ci_test:
      type: snowflake
      account: "{{ env_var('DESTINATION__SNOWFLAKE__CREDENTIALS__HOST') }}"
      user: RAYS_ANALYTICS_CI_SERVICE
      private_key_path: ~/.ssh/ci_service_user_rsa_key_p8.pem
      role: SYSADMIN
      database: RAYS_ANALYTICS
      warehouse: COMPUTE_WH
      schema: PROD
      threads: 4
```

Mirrors `dev`, but authenticates as `RAYS_ANALYTICS_CI_SERVICE` with its own key path instead of `DBT_SERVICE_USER`.

**Gotchas carried over from the original WIF setup:**
- `CREATE USER` / `CREATE AUTHENTICATION POLICY` are `SECURITYADMIN`/`USERADMIN` territory, not `SYSADMIN`.
- `DEFAULT_ROLE` on `CREATE USER` doesn't grant the role — needs an explicit `GRANT ROLE ... TO USER`.
- `AUTHENTICATION POLICY` is schema-scoped.
- `ALTER USER ... SET AUTHENTICATION POLICY` takes no `=`.
- `DESCRIBE USER` doesn't surface policy attachment — use `INFORMATION_SCHEMA.POLICY_REFERENCES`.

Full original WIF setup SQL (CREATE USER/OIDC block) preserved in CHANGELOG.md for history.

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

Litmus test: *who/what can authenticate* → `SECURITYADMIN`. *Data/compute objects* → `SYSADMIN`. `ACCOUNTADMIN` inherits both, which is why it "just works" regardless of domain — worth resisting as a default since it papers over which branch owns a task.

**Default role decision:** `SYSADMIN` is the default Snowsight role going forward, not `ACCOUNTADMIN`. Set via:
```sql
ALTER USER <username> SET DEFAULT_ROLE = SYSADMIN;
```
`ACCOUNTADMIN` is reserved for genuinely account-level tasks: resource monitors, billing, rare service-account/user management. Full four-role rotation is enterprise ceremony not worth it solo — two roles is right-sized here.

**The gotcha (bit three times — twice in Phase 3, once in Phase 4):** anything created via Snowsight UI is owned by whatever role the session defaults to. If that's `ACCOUNTADMIN` and `DBT_SERVICE_USER` runs as `SYSADMIN`, `SYSADMIN` has zero automatic access. Hit at three object levels (table, warehouse, schema), each a distinct error — full text: see CHANGELOG.md.

**Fix, any case:** `GRANT <privilege> ON <object> TO ROLE SYSADMIN`, run as the object's owning role. Better fix: switch the Snowsight role selector to `SYSADMIN` *before* manual UI work, so objects are owned right from creation.

---

### Bronze Layer & Iceberg Catalog Notes

Bonus-track, not actively worked. Architecture (when revisited): S3 (us-east-2) Iceberg tables cataloged via Snowflake Open Catalog, Snowflake/DuckDB reading the same location as separate engines. Deferred, not rejected — self-hosted Polaris is a low-friction switch later (same software). Full details: see CHANGELOG.md.

---

### Snowsight Navigation (as of June 2026)

Databases → Catalog → Database Explorer; SQL editor is Projects → Workspaces (renamed from Worksheets). **Caveat:** shifts often, re-check before trusting long-term.

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
  pipelines/
    mlb_games.py                ← dlt pipeline, MLB Stats API → DuckDB/Snowflake (--destination flag)
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
- **Raw table:** `RAYS_ANALYTICS.RAW.GAMES` in Snowflake — populated by `pipelines/mlb_games.py` (`--destination snowflake`), owned by `SYSADMIN`. Phase 3 manual-CSV-stopgap table fully retired.
- **Rays team ID:** 139
- **Seasons loaded:** 2022–2026 (~740 completed games; 162 each for 2022–2025, 92 for the still-in-progress 2026 season, growing run-over-run)
- **Star schema:** stg_games → dim_teams, dim_venues, fct_games
- **48 tests** — not_null, unique, accepted_values, relationships

---

### Workflow Conventions

- **Repo-root + `--project-dir`, not `cd rays_analytics` (revised July 2026).** `.env` is at repo root; `dbt_project.yml` is in `rays_analytics/`. dbt v1.12+'s native `.env` autoload is CWD-bound with no `--project-dir` support, so it won't fit this repo's multi-tool layout even post-upgrade. Standardized on Makefile targets that run from repo root, explicitly load `.env` via `uv run --env-file .env`, and pass `--project-dir rays_analytics`.
- **Makefile targets** (repo root): `make setup` (`uv sync --locked`), `make dbt-build` (`uv run --env-file .env dbt build --project-dir rays_analytics`), `make dbt-debug-ci` (same, `dbt debug --target ci_test`).
- Session start: `cd ~/projects/rays-analytics && source .venv/bin/activate` — no further `cd` needed.
- (Optional, personal) `direnv` auto-loads `.env` on `cd` — not in the required onboarding path, `direnv allow`'s prompt reads like a broken repo to a first-time cloner.
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
- **State-based selective builds as the default local workflow (decided August 2026):** `dbt build --select state:modified+` is now the default for local iteration (not just Phase 8 CI) to control Snowflake credit spend now that DuckDB isn't free local compute (see DuckDB-dropped decision above). Full-project `dbt build` stays appropriate before opening a PR.
- **Repo audited clean (June 2026)** via `git log --all --oneline -- profiles.yml '*.pem' '*.key' '*.env'` (empty) — worth re-running periodically.
- **One-off exports never get committed** — `.gitignore` covers `/games_export.csv` and `/scratch/` for throwaway dumps.

---

### CI Architecture Notes

`.github/workflows/ci.yml` has **two jobs**, both against Snowflake, no DuckDB (implemented September 2026): `pull_request` runs a full `dbt build` against `DEV`; `push` to `main` runs a full `dbt build` against `PROD`. Both authenticate via key-pair, `private_key` passed inline from `SNOWFLAKE_PRIVATE_KEY` (no key file, no `id-token: write`). `dev_duck` target and `make dbt-build-duckdb` fully removed, not kept as fallback — reviving them reintroduces the dialect-portability problem dropping DuckDB solved.

**PR job on `state:modified+` — on the horizon, not yet wired (September 2026):** attempted during the DuckDB-removal PR, reverted to a full build — `state:modified+` needs a comparison `manifest.json` to diff against, and CI has no mechanism to produce or fetch one yet (`Runtime Error: Got a state selector method, but no comparison manifest`). Two candidate sourcing approaches, neither evaluated in depth: (a) upload `manifest.json` as a GitHub Actions artifact from the merge job, fetched by the PR job via a cross-workflow-run artifact download; (b) piggyback on the existing `gh-pages` docs publish to also host `manifest.json` alongside the dbt docs site, fetched via plain HTTP in the PR job. Deliberately low-priority — full builds are cheap at the current model count (4), revisit once that stops being true. `RAYS_ANALYTICS_DEV`/`DEV_ROLE` and `RAYS_ANALYTICS`/`CI_DEPLOYER` two-database split below is a separate, still-deferred piece of this same post-DuckDB design.

**`games_pipeline.yml` — production scheduling implemented (September 2026):** daily cron (6:47am Eastern, DST-safe `timezone:` field) plus `workflow_dispatch`. Runs the current-season `games` dlt pipeline, then `dbt deps` → `dbt source freshness` → full `dbt build`, against Snowflake `PROD`, same inline `private_key` pattern as `ci.yml`. `concurrency: {group: games-pipeline, cancel-in-progress: false}` stops a stray dispatch racing the cron — `false` since dlt's SIGTERM handling is graceful shutdown, not safe mid-load cancellation. `dbt source freshness` is a sanity check, not a true staleness gate: `games()`'s full re-pull + merge means a successful run always updates `_dlt_loads`, so it can't distinguish "genuinely new data" from "ran, found nothing new" — revisit with a real `incremental()` cursor. Run-failure alerting not designed — see Current Status.

**Why `ci.yml` doesn't call `make dbt-build` (deliberate):** `make dbt-build` assumes a local `.env` (`uv run --env-file .env`), which CI intentionally doesn't have — `ci.yml` generates `~/.dbt/profiles.yml` from GitHub Secrets instead. Both jobs' `working-directory: rays_analytics` + bare `dbt build` is correct — don't "fix" this to call the Makefile target, it would break the job.

**Known gap:** green means "code correct," not "Snowflake data fresh" — doesn't re-run the dlt pipeline. Closes once Phase 5's GitHub-Actions-based observability design lands (a standalone `dbt source freshness` task or similar, now that the Dagster asset-checks plan is off the table — see Phase 5).

**Running under `SYSADMIN`, not scoped down (flagged July 2026, design only, not implemented):** broader than the job needs. Planned fix is a two-database, two-role split — `RAYS_ANALYTICS_DEV`/`DEV_ROLE` (broad access) and `RAYS_ANALYTICS`/`CI_DEPLOYER` (scoped, warehouse usage + schema-level create/write only) — replacing the current schema-only `RAW`/`DEV`/`PROD` split in one database. Deprioritized behind the README/walkthrough and a baseball-question mart.

**Actions pinning:** All actions pinned to exact commit hashes, not floating tags — the March 2025 tj-actions/changed-files compromise (secrets leaked via a hijacked tag) is the canonical reason. Current pinned hashes:
- `actions/checkout` v6.0.2 → `de0fac2e4500dabe0009e67214ff5f5447ce83dd`
- `astral-sh/setup-uv` v8.1.0 → `08807647e7069bb48b6ef5acd8ec9567f424441b`

**Dependency installation/auditing:** `uv sync --locked` (fails on `uv.lock`/`pyproject.toml` drift); `uv audit` runs as a CI step, PR job only, built into uv 0.10.12+.

**`uv audit` can fail a PR for reasons unrelated to that PR** — it audits whatever's pinned in `uv.lock`, so a newly-disclosed CVE against an already-resolved dependency can fail an unrelated change (hit twice: `cryptography`/`msgpack` on a docs PR, `snowflake-connector-python`/CVE-2026-15925 on a CI-rewrite PR). Fix is a narrow lockfile bump from repo root (`uv.lock` lives at root, not `rays_analytics/`): `uv lock --upgrade-package <name> && uv sync --locked`.

**`sqlparse` CVEs suppressed, not fixed (August 2026, five GHSAs as of September 2026):** dbt-core pins `sqlparse<0.6.0` on every release checked (1.11.11, latest 1.12.2), blocking the patched 0.6.0 — not fixable by a dbt-core bump. Suppressed via `[tool.uv.audit] ignore = [...]` in `pyproject.toml` (plain `ignore`, not `ignore-until-fixed`, which only applies while the library itself has no fix), most recently adding `GHSA-cfqr-cjx5-5jcm`. Tracking: `dbt-labs/dbt-core#12329`. Resolves via dbt-core relaxing the pin, or a future move to dbt-core v2/Fusion (drops sqlparse entirely) — not a reason to pull v2 forward while it's alpha/beta.

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

#### Phase 4 — Ingestion (~1 week, slimmed for core path) ✅ COMPLETE

**Goal:** Replace `load_mlb_data.py` with a dlt pipeline writing directly into `RAYS_ANALYTICS.RAW`, no bronze/Iceberg layer in this pass. Full history and completed-items lists: see CHANGELOG.md. Open follow-ups from this phase now live in Current Status, below.

**Skills locked in (core):** Python-based ingestion, dlt resource/source/pipeline model, raw/staging layer pattern, merge write-disposition, destination-parameterized pipeline design, schema drift handling.

**Skills locked in (bonus, when revisited):** Iceberg format and REST catalog mechanics, S3/IAM setup, storage-layer portability, incremental loading with a real cursor.

---

#### Phase 5 — Orchestration and Observability — CORE, reversed to GitHub Actions August 2026

**What was attempted:** self-hosted Dagster OSS on a DigitalOcean VPS via Docker Compose (webserver, daemon, user-code gRPC server, Postgres + Tailscale sidecar). Fully built and deployed — droplet provisioned/hardened, all five containers clean, Tailscale sidecar joined the tailnet.

**Why it was abandoned:** the MLB Stats API blocks DigitalOcean's IP range at the CDN level — confirmed via multi-environment testing, not fixable from within the stack. Unreachable from any DigitalOcean-hosted process, so the VPS is a dead end regardless of orchestrator.

**Resolution:** production scheduling now runs on `games_pipeline.yml` (GitHub Actions + dbt/dlt native tooling) — see CI Architecture Notes. `ci.yml` keeps its unrelated PR/merge-time gate role.

**Full detail preserved:** complete prior implementation + retrospective on `archive/phase-5-dagster-vps`. Decision narrative, the daemon bug, and the IP-blocking discovery: CHANGELOG.md.

**Skills locked in:** Docker Compose multi-service stacks, Tailscale sidecar networking, VPS provisioning/hardening, Compose-environment credential handling, isolating a network-level blocker via multi-environment testing.

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

**Phase 4 complete.** Phase 5's Dagster/VPS attempt is fully cleaned up off `main` — see Phase 5 above for why it was abandoned. The `orchestration/` directory, the `dagster`/`dagster-dbt`/`dagster-dlt`/`dagster-postgres` extra in `pyproject.toml`, and the Dagster-specific module-level objects in `pipelines/mlb_games.py` are removed; full prior implementation preserved on `archive/phase-5-dagster-vps`. `ci.yml` is Snowflake-only (September 2026); local `profiles.yml`/Makefile DuckDB scratchpad cleanup still not done.

**Still open:** run-failure alerting for `games_pipeline.yml` not designed — a failed run just sits red in the Actions tab.

**Next actions:**
1. Design run-failure alerting for `games_pipeline.yml` (email/Slack/etc. on a failed scheduled run)
2. Design "run succeeded but data is wrong" observability beyond the current sanity-only freshness check — no orchestrator-native asset checks anymore, needs its own approach (e.g. Elementary)
3. Decide the next data source to add — Statcast/pybaseball no longer assumed by default
4. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence

**Deferred, no target phase:**
- `CI_DEPLOYER` role-scoping and the two-database split, `state:modified+` in CI — all designed, see CI Architecture Notes, not implemented
- Next data source will need dlt's real `incremental()` cursor pattern (`games` doesn't use it)
- Deliberately introduce a schema change and observe dlt/dbt source freshness response — not yet done

Full session-by-session history: see CHANGELOG.md.
