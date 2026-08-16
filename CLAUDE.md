# Rays Analytics — Project Instructions

---

## Part 1 — Stable Reference

*This section changes rarely. It covers who I am, how the environment is set up, what tools are in the stack and why, and what was ruled out. Update only when a fundamental decision changes.*

---

### About Me

I started this project with dbt and BI experience but no hands-on modern cloud warehouse experience — this project is where that's been built. Goal: a complete, portfolio-ready modern ELT stack for learning and career development. I prefer to understand what I'm doing rather than just following commands.

**Why I'm actually doing this project:** Curiosity and enjoyment. Job marketability is real and welcome but not the filter for what's worth exploring — don't gate discussing/prototyping an idea behind "does this earn its place." That scrutiny is for what becomes permanent, maintained stack infrastructure. Default to following interesting tangents.

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

**Docker is no longer avoided outright (reversed August 2026).** Originally ruled out on the Mac Mini's 16GB RAM ceiling. Docker now runs via Docker Compose on a separate VPS for self-hosted Dagster OSS (decided August 2026 — see Orchestration Hosting decision in Key Architectural Decisions), not on the Mac Mini, so that constraint no longer applies anywhere Docker is actually used. The Mac Mini itself still runs no containers.

**`profiles.yml` lives at `~/.dbt/profiles.yml`** — never committed. Points to Snowflake DEV schema; DuckDB target retained as `dev_duck`.

**DuckDB path is always relative** (`dev.duckdb`) from repo root, never hardcoded absolute. `DUCKDB_PATH` overrides it in CI.

**UV does not load `.env` files automatically.** Use `uv run --env-file .env <command>` to load them explicitly — works for any command in the venv (e.g. `uv run --env-file .env dbt build`). For scripts needing env vars at import time, use python-dotenv: `from dotenv import load_dotenv; load_dotenv()`.

---

### The Stack

| Layer | Tool | Status | Notes |
|---|---|---|---|
| Ingestion | dlt | **Running** | Python library, no Docker |
| Bronze storage | Amazon S3 | Bonus track, not started | Same region as Snowflake (us-east-2); raw Iceberg tables, engine-agnostic |
| Iceberg catalog | Snowflake Open Catalog (managed Apache Polaris) | Bonus track, not started | Free during current billing period; resolves CI reachability; same software as self-hosted Polaris if revisited later |
| Warehouse (local dev) | DuckDB | Demoted, ad hoc scratchpad only | Dropped as a dbt build target (decided August 2026) — see Key Architectural Decisions. CLI/Marimo queries only now, same non-build role DBeaver was already excluded from. **ci.yml/Makefile/profiles.yml still reflect the old DuckDB-build pattern — updating them is a decided-not-yet-implemented follow-up, see Current Status** |
| Warehouse (cloud) | Snowflake | **Running** | ~$35–55/month, X-Small, 60-sec auto-suspend — raised from ~$30–40 now that dbt builds exclusively against Snowflake (dev + prod), no DuckDB target to offload local iteration onto |
| Transformation | dbt Core + dbt-snowflake | **Running** | Snowflake-only build target as of August 2026 — see Key Architectural Decisions |
| Semantic layer | MetricFlow + Cube Core/Cloud free | Planned, Phase 6 | Cube's necessity under reconsideration — see Key Architectural Decisions |
| Orchestration | Dagster OSS (self-hosted, Docker Compose on a VPS) | Decided, not yet implemented | Tool chosen July 2026; hosting decided August 2026 (VPS + Docker Compose, four services + Tailscale — supersedes the earlier Mac Mini/launchd plan) — see Key Architectural Decisions. GitHub Actions cron is still the only scheduler actually running today |
| Observability | Dagster asset checks | Decided, not yet implemented | Depends on Dagster setup above. Elementary now optional, future dbt-test-anomaly-detection decision only |
| BI | Evidence | Planned, Phase 6 | Code-first, Git-native — not yet installed or configured |
| Version control + CI | GitHub + GitHub Actions | **Running** | |
| Notebooks | Marimo | Planned | Not yet added to `pyproject.toml` despite an earlier "Added in Phase 4" note — corrected here |
| AI development | Claude Pro + Claude Code + Anthropic API | Planned, Phase 7+ | Claude Code itself is in active use for this project; the Phase 7 AI-layer integration (Cortex Analyst, API-driven querying) hasn't started |

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

**Estimated monthly cost: ~$65–95/month + an undecided VPS cost** — Snowflake ~$35–55 (raised from ~$30–40 now that DuckDB is dropped as a dbt build target — estimated $5–15/month in added compute, mostly absorbed by the 60-second minimum billing floor given this project's low query volume and short build times), Cortex ~$5–15, Claude Pro $20, Anthropic API (Phase 7+) ~$5–10, rest free. **VPS provider/size for self-hosted Dagster is not yet decided** (Hetzner discussed favorably on cost) — flagged as an open decision, not estimated here.

---

### Key Architectural Decisions

Full reasoning and alternatives considered for settled decisions: see CHANGELOG.md.

**Why dlt over Airbyte:** Airbyte is Docker-heavy with an uncertain free tier; dlt teaches ingestion at code level instead of abstracting it behind a UI.

**Why dlt over Snowflake Openflow (resolved June 2026):** Openflow fits its ~20 supported connectors with no customization needed; MLB Stats API and pybaseball/Statcast are bespoke sources outside that list, and Openflow needs real infrastructure (BYOC/Snowpark Container Services) that cuts against the RAM ceiling.

**Why MetricFlow + Cube over dbt Cloud:** MetricFlow is the OSI v1.0 reference implementation for semantic layers; Cube provides the API exposure layer dbt Cloud would otherwise lock behind $100/month. See CHANGELOG.md for full reasoning.

**Cube's necessity reconsidered (added June 2026):** Cube exposes governed metrics over an API — it isn't itself a self-serve dashboard tool. MetricFlow + Snowflake Semantic Views stay core regardless; Cube is now optional pending the Phase 6 BI-tool decision.

**Why Dagster OSS, self-hosted, over Dagster Cloud, Prefect OSS, and Prefect Cloud Hobby tier (decided July 2026, resolved from "under re-evaluation"):** Dagster Cloud removed free credits from Solo/Starter plans May 1, 2026 (per-asset billing from zero, no grandfathering) — ruled out on cost grounds alone. Between Dagster OSS and Prefect (OSS or Cloud Hobby), Dagster OSS won: stronger comp/market signal for DE-adjacent AE roles at smaller/mid-market companies, more Python surface area (assets, resources, IO managers vs. Prefect's simpler flow/task decorators), and `dagster-dbt` auto-generates one asset per dbt model from `manifest.json` — preserves the existing dbt DAG with no remodeling. Fully self-hosted, so no new vendor-pricing risk. Supersedes the July 2026 "GitHub Actions cron" decision below for production scheduling — GitHub Actions keeps its existing PR/merge-time code-correctness gate role unchanged. **Hosting location reversed August 2026 — see Orchestration Hosting decision immediately below; the Mac Mini/SQLite/launchd plan described in the original July 2026 decision no longer applies.** Full comparison against Prefect OSS/Cloud and Kestra, plus the Prefect/Dagster acquisition context: see CHANGELOG.md.

**Dagster Cloud Solo/Starter, re-confirmed disqualifying with the actual math (decided August 2026):** Prior doc text ruled Dagster Cloud out citing the May 2026 pay-as-you-go pricing change generally. This session did the math: Solo is $10/month base plus $0.04/credit, where 1 credit = 1 asset materialization or op execution. `dagster-dbt` generates one Dagster asset *per dbt model*, not one per project — at this project's ~48 dbt models plus dlt source assets, that's roughly 49 assets. A comparable published example (50 dbt models, materialized once daily) runs ~1,500 credits/month, or ~$60/month in credits alone before the base fee — nearly this entire project's monthly budget on orchestration alone. Also considered and rejected: Dagster+ Serverless (adds a further $0.010/min compute charge on top of credits) and Dagster+ Hybrid with a local agent (removes the serverless charge and would have fit the no-Docker-on-Mac-Mini constraint that existed at the time, but credit billing is driven by asset count regardless of which agent runs the code — doesn't fix the core cost problem).

**Orchestration hosting: self-hosted Dagster OSS on a small VPS via Docker Compose, not the Mac Mini (decided August 2026, supersedes the Mac Mini/launchd plan in the July 2026 Dagster decision and in Phase 5 below):**

*Why the Mac Mini is out:* keeping the Mac Mini continuously powered on for the daemon doesn't work in practice — this was tested, not theoretical — and remote access to it when not physically at hand is a significant practical pain, defeating the point of always-on orchestration. Same plainly-stated reversal pattern as the WIF→key-pair and GitHub-Actions-cron reversals elsewhere in this doc: the original plan looked sound on paper and didn't hold up in practice.

*Why GitHub Actions cron isn't the long-term answer either:* separate from its already-documented reliability concerns (scheduler delays since February 2026, 60-day-inactivity auto-disable), it doesn't teach the actual orchestration principles this phase exists to build — asset graph, lineage, dbt-model-level asset checks.

*Why Docker is back in scope:* "Docker is intentionally avoided" is reversed — see Key Environment Decisions. It now runs on the VPS, not the Mac Mini, so the original 16GB RAM ceiling reasoning doesn't apply to it.

*AWS-native deployment (EC2/ECS/RDS/S3 IO manager, per Dagster's official AWS deployment guide) — evaluated and rejected:* EC2-hosted Docker Compose is architecturally identical to the VPS plan but at higher cost; ECS adds a large surface of AWS-specific complexity (task definitions, IAM roles, VPC/subnet config, Fargate/EC2 launch types) built for concurrent-scaling workloads this solo, ~daily pipeline doesn't have; RDS was considered specifically for automated Postgres backups but rejected in favor of the VPS provider's built-in automated backup feature (simpler, cheaper, no second cloud vendor relationship); S3 as a Dagster I/O manager is a different feature entirely (passing data between ops during parallel execution) that doesn't apply to this pipeline's shape.

*Architecture, decided:* four services under Docker Compose, not three — `dagster-webserver`, `dagster-daemon`, a dedicated user-code gRPC server (loads/executes pipeline code, kept separate from the webserver/daemon), and Postgres for run/event storage.

*Why Postgres, not S3 or Snowflake, for run/event storage:* Dagster's storage layer only implements a real run/event backend for SQLite, Postgres, or MySQL — no S3 or Snowflake backend exists at all. Snowflake specifically would also be economically wrong for this workload even if it existed: run/event writes are frequent small transactions (every materialization, every sensor tick), the opposite shape from Snowflake's batch-scan/warehouse-second billing model — this would recreate the same credit-cost problem that ruled out Dagster Cloud, just self-inflicted via the Snowflake bill instead.

*Why Postgres, not SQLite-on-a-volume:* considered as the simpler option and rejected — Dagster's own docs recommend Postgres for production given SQLite's single-writer limitation, and three processes (webserver, daemon, user-code server) will be hitting this store concurrently.

*Why self-hosted Postgres, not a managed free tier (Neon, Supabase):* Neon's core value (scale-to-zero) doesn't apply since Dagster's daemon polls continuously and compute never idles — the free tier's ~100 CU-hours/month would be exhausted in days. Supabase's free tier caps at 500MB and pauses inactive projects. Both also reintroduce the external-vendor-free-tier risk already rejected twice (Dagster Cloud, Prefect Cloud Hobby).

*Remote access:* Tailscale, run as a Docker Compose sidecar container (`network_mode: service:tailscale`) attached to the webserver. The webserver container never binds a public port — reachable only via the tailnet. A sidecar, not a bolt-on VPN layer.

*Run/event history durability posture, decided:* accept provider-level automated backups (e.g. ~20% of instance cost on Hetzner, full-disk snapshot, no custom backup pipeline) as sufficient, or accept losing run history entirely on VPS failure as a real but low-stakes outcome. This is low-stakes because actual pipeline data lives in Snowflake, dlt state lives in destination-system tables, and all code/config lives in Git — none of that is at risk on VPS failure. Only the orchestration run/event timeline is VPS-local, and losing it just means an empty history that repopulates from the next successful run. A custom `pg_dump`/WAL-G backup pipeline was researched and explicitly **not** chosen, in favor of the simpler options above.

*Optional, not required:* `S3ComputeLogManager` to stream compute logs (stdout/stderr) to S3, reusing credentials from the Iceberg bonus track — a nice-to-have addition, not a Phase 5 dependency.

*Still open, not decided this session:* the specific VPS provider, region, and instance size. Hetzner was discussed favorably on cost but nothing is committed — a next-session decision, not a name to guess at here.

**Why S3 + Iceberg + Snowflake Open Catalog over self-hosted Polaris or AWS Glue (decided June 2026; rescoped to bonus track):** Open Catalog is a managed hosting of the actual open-source Apache Polaris, free during the current billing period and reachable by both local dev and CI (unlike self-hosted Polaris on the Mac Mini) while staying open-source-first (unlike AWS Glue). Core Phase 4 skips this entirely — dlt writes straight into Snowflake `RAW`, no bronze layer. Full three-way comparison and reasoning: see CHANGELOG.md.

**Why Evidence over Metabase:** Code-first, Git-native, fits the everything-as-code philosophy. Cube Cloud free tier is dev/test only — Cube Core runs as a local Node process at zero cost if needed.

**Public self-serve demo, added June 2026:** Evidence ships a DuckDB engine to the browser via WebAssembly (Universal SQL) — a static GitHub Pages site built from exported Parquet snapshots lets any visitor run live SQL client-side, no backend/credentials/per-visitor cost. Separate from the internal BI decision below. Perspective (FINOS) is the fallback if drag-and-drop pivoting matters more than filter-driven interactivity.

**Self-serve BI tool decision, added June 2026, deferred to Phase 6:** Lightdash reads metrics directly from dbt YAML for a genuine point-and-click explorer, but self-hosting needs Docker (conflicts with no-Docker stance) vs. Metabase (no Docker, but metrics live outside dbt). Not yet decided.

**dlt resource design for `games` — completed games only, no live/in-progress state (decided June 2026):** The `games` resource filters to `Final`/`Completed Early` before yielding, so unplayed or in-progress games never reach `raw.games` — a deliberate scope call, not a technical limitation. Full reasoning: see CHANGELOG.md.

**Why `games` doesn't use dlt's `incremental()` cursor (decided June 2026):** The schedule endpoint doesn't expose a true modified-since cursor and returns the whole season every call regardless, so `games` uses full-season re-pull + `merge` write-disposition keyed on `game_pk` instead. **This will not hold at Statcast scale** — see Phase 4 notes; pitch-level data has real cursor potential (game date) and re-pulling full history every run isn't viable at that volume. Full reasoning: see CHANGELOG.md.

**dlt pipeline destination is parameterized, not hardcoded (decided June 2026):** `mlb_pipeline.py` takes `--destination duckdb|snowflake` as a CLI flag (default `duckdb`). Only the `pipeline.run()` destination argument changes — chosen so DuckDB refreshes freely at zero cost while Snowflake compute is only spent when explicitly requested. CI's DuckDB and Snowflake jobs will call the same script with different flags.

**DuckDB dropped as a dbt build target (decided August 2026):** dbt now builds only against Snowflake (dev and prod). DuckDB is demoted to an ad hoc query scratchpad only (CLI / Marimo) — the same non-build role DBeaver was already excluded from. The original multi-engine goal — S3 as home base, swap compute engines freely — doesn't pay for itself at this project's size: it forced permanent dialect-portability discipline (routing everything through `dbt_date` instead of native SQL) and blocked dbt's `ref()` from working normally across a two-engine split. The added Snowflake compute cost is small (est. $5–15/month at XS warehouse, given this project's low query volume and short build times — mostly under the 60-second minimum billing floor). **Follow-up not done this session:** `ci.yml`'s DuckDB-on-every-PR job, `profiles.yml`'s `dev_duck` target, and the `make dbt-build-duckdb` Makefile target all still reflect the old dual-target pattern — updating them to match this decision is a decided-not-yet-implemented item, same pattern as `CI_DEPLOYER` role-scoping below. See Current Status for tracking.

**Delta Lake table format — evaluated and rejected (decided August 2026):** Considered as an alternative to dedup-via-dbt-intermediate-model for a future bronze layer. Rejected: the added complexity (a `delta-rs` dependency, Snowflake reading Delta tables via Delta Direct or Iceberg-wrapping) isn't offset by removing a well-understood, testable dbt dedup step, and it's Databricks-flavored — lower job-market signal for this project's target roles than the Iceberg bonus track already planned, which covers the same "open table format with merge" learning goal.

**dlt table ownership gotcha (hit June 2026, again on Snowflake July 2026):** dlt cannot retrofit its tracking columns (`_dlt_id`, `_dlt_load_id`) onto a table it didn't create (DuckDB: `Parser Error: Adding columns with constraints not yet supported`). Fix: any table dlt owns must be created by dlt from a clean slate — drop it and let the pipeline recreate it.

**`dim_teams`/`dim_venues` deduplication — most-recent-name-wins (decided June 2026):** Team/venue names can change over time for the same numeric id (relocation, sponsorship renames), which broke a plain `(id, name)` dedup. Fixed by ranking rows per id by `game_date desc` and keeping only the most recent name. Full reasoning and alternatives considered: see CHANGELOG.md.

**Secrets consolidation — single `.env` shared by dbt and dlt, no `.dlt/secrets.toml` (decided July 2026):** dlt and dbt each kept a separate credential store for the same Snowflake account/service user. Both now read one gitignored `.env` at repo root: dlt via `DESTINATION__SNOWFLAKE__CREDENTIALS__*` env vars, dbt via `env_var()` in `profiles.yml` (see Current `profiles.yml` structure below). GitHub Secrets for CI stay a separate third location. Full reasoning: see CHANGELOG.md.

**Why 16GB Mac Mini is sufficient (reworded August 2026):** Docker no longer runs on the Mac Mini — it runs via Docker Compose on a separate VPS for self-hosted Dagster (see Orchestration Hosting decision above). The Mac Mini's RAM ceiling isn't the reason Docker is or isn't used anywhere in the stack anymore; the Mac Mini itself still runs everything else (dbt, dlt, VS Code, DuckDB CLI/Marimo scratchpad use) as plain Python or Node processes, no containers.

**GitHub Actions cron scheduling decision, superseded (decided July 2026, reversed July 2026, hosting further revised August 2026):** an earlier session kept GitHub Actions cron for production scheduling rather than pulling Dagster/Prefect forward, reasoning that a missed/failed scheduled run risked a "silent watermark gap" once Statcast's real incremental cursor was in play. **That framing was overstated and is corrected here:** as long as the incremental cursor state is stored durably (dlt already does this via pipeline state) and write-disposition is `merge` on a stable key, a missed run just means the next successful run pulls a larger window and self-heals — Baseball Savant/Statcast data doesn't expire, so there's no source-side retention risk. GitHub Actions cron reliability concerns (scheduler delays since February 2026; auto-disables scheduled workflows after 60 days of repo inactivity) were real, but the decision to move to Dagster OSS (see above) was made for long-term architecture, extensibility, and career-signal reasons — not because the cron approach would have caused data loss. `workflow_dispatch:` fallback and the GH Actions dead-man's-switch concern are no longer needed for the scheduling mechanism itself, since Dagster's daemon isn't dependent on GitHub's scheduler. **The `launchd` LaunchAgent consideration from the original July 2026 version of this decision is removed as of August 2026** — it was specific to surviving Mac reboots, which no longer applies now that Dagster runs on a VPS, not the Mac Mini (see Orchestration Hosting decision above). The failure mode in its place is **VPS downtime**, not Mac downtime: a quick VPS restart is a non-event (Docker Compose restarts the four services); extended VPS downtime is the real concern — self-heals for `games` (full re-pull pattern) but would not self-heal once Statcast-equivalent data uses a true incremental cursor, same risk shape as a missed GH Actions run would have had. An external heartbeat/dead-man's-switch is still a reasonable future addition, just decoupled from the orchestrator choice.

**Why key-pair for CI Snowflake auth (reversed July 2026):** see Snowflake CI Auth Notes below for full reasoning. Short version: the original WIF plan assumed `dbt-snowflake` shipped WIF support in May 2026 — checked directly against `dbt-labs/dbt-adapters` PR #1316, which is still open/unmerged as of July 2026, blocked on a maintainer requirement for ongoing integration-test infrastructure. No stable or pre-release `dbt-snowflake` has WIF support. Reversed to key-pair — matches dlt, which also has no WIF support, so no asymmetry.

**dbt Core vs dbt Fusion vs dbt Core v2.0:** dbt Labs open-sourced the Fusion runtime as dbt Core v2.0 under Apache 2.0 at Summit June 2026. v2.0 is alpha; dbt Core v1.11.x remains the right choice for now. dbt Core v1.12 (beta) ships the same Fusion parser via `dbt parse --use-v2-parser` as a dry-run compatibility check. Revisit at Phase 8.

**Snowflake-native dbt:** GA November 2025. No additional licensing cost — pay only warehouse credits. Worth exploring alongside the local dbt workflow in Phase 3.

**Snowflake Semantic Views:** Standard SQL querying GA March 2026. Zero extra cost, zero infrastructure overhead. Snowflake-only, but this stack is Snowflake-only in production.

**dbt/Fivetran merger:** Completed June 1, 2026 (Fraser CEO, Handy President). dbt Core remains Apache 2.0; no impact on this stack. Long-term Core-vs-commercial investment balance bears watching.

**Prefect/Dagster acquisition (noted July 2026):** Prefect acquired Dagster Labs, announced July 13, 2026; the combined company operates under the Prefect name starting August 2026. Both products currently keep their name, license (Apache 2.0), and roadmap per official statements. Dagster founder Nick Schrock has departed. Doesn't change the Phase 5 Dagster OSS decision above, but worth watching as long-term vendor-risk framing for that choice.

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
| MotherDuck | Third portability target considered June 2026; deprioritized — work-related interest, not project-specific |
| AWS Glue | Considered for the Iceberg catalog; zero-ops but proprietary |
| Airflow | Common in AE postings but not required — concepts transfer from Dagster/Prefect |
| Delta Lake | Considered August 2026 as a bronze-layer dedup alternative; added complexity (`delta-rs`, Snowflake Delta-read path) not worth removing a well-understood dbt dedup step, and Databricks-flavored — lower job-market signal here than the Iceberg bonus track covering the same learning goal |
| AWS-native orchestration hosting (EC2/ECS/RDS) | Considered August 2026 for Dagster hosting; ECS's AWS-specific complexity doesn't fit a solo ~daily pipeline, RDS backups duplicate the VPS provider's built-in backup feature — see Orchestration Hosting decision |

**Docker note (reversed August 2026):** Docker is no longer categorically excluded — see Key Environment Decisions and the Orchestration Hosting decision in Key Architectural Decisions. It now runs via Docker Compose on a VPS for self-hosted Dagster; the Mac Mini itself still runs no containers.

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

**Decision (reversed July 2026):** the Snowflake-on-merge CI job authenticates via key-pair, not WIF. The "PR merged May 20, 2026" claim was wrong — `dbt-labs/dbt-adapters` PR #1316 ("Adding support for Snowflake Workload Identity Federation") is still open, open since September 2025, blocked on a maintainer requirement for ongoing integration-test infrastructure. The dbt-snowflake v1.12.0 milestone shows it open at 45% complete. Reversed to key-pair — both dlt and dbt now use key-pair in CI, no asymmetry.

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

Mirrors the `dev` Snowflake target, but authenticates as `RAYS_ANALYTICS_CI_SERVICE` (the CI service user) with its own key path, instead of `DBT_SERVICE_USER`.

**Gotchas carried over from the original WIF setup, still relevant to this user:**
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
- **State-based selective builds as the default local workflow (decided August 2026):** `dbt build --select state:modified+` is now the default for local iteration, not just a Phase 8 CI optimization — specifically to control Snowflake credit consumption from frequent local dev now that DuckDB is no longer free-tier local compute for dbt builds (see DuckDB-dropped-as-build-target decision in Key Architectural Decisions). Full-project `dbt build` stays appropriate before opening a PR.
- **Repo audited clean (June 2026):** confirmed via `git ls-files` and `git log --all --oneline -- profiles.yml '*.pem' '*.key' '*.env'` (empty). Worth re-running periodically.
- **One-off exports never get committed.** `.gitignore` includes `/games_export.csv` and `/scratch/` for throwaway dumps — delete when done or park in `/scratch/`.

---

### CI Architecture Notes

`.github/workflows/ci.yml` has **two jobs**. First: `pull_request` to `main`, `dbt build` against DuckDB after `mlb_pipeline.py --destination duckdb`. Second: `push` to `main` (post-merge), `dbt build` against real Snowflake via key-pair (reversed from WIF — see Snowflake CI Auth Notes above). DuckDB on every PR; Snowflake compute bounded to once per merge.

**Why `ci.yml` doesn't call `make dbt-build` (deliberate, not a leftover from before the Makefile existed):** `make dbt-build` assumes a local `.env` file (`uv run --env-file .env`), which CI intentionally doesn't have — `ci.yml` generates `~/.dbt/profiles.yml` directly from GitHub Secrets instead. So both jobs' `working-directory: rays_analytics` + bare `dbt build` is the correct, intended pattern — don't "fix" this to call the Makefile target, it would break the job.

**Snowflake job steps:** writes `SNOWFLAKE_PRIVATE_KEY` to `$RUNNER_TEMP/ci_key.pem` (chmod 600, never logged), generates `profiles.yml` with `user`/`account` from Secrets and `role`/`database`/`warehouse`/`schema` hardcoded (non-sensitive), runs `dbt build`. No `id-token: write` — key-pair doesn't use OIDC.

**Known gap:** green means "code correct," not "Snowflake data fresh" — doesn't re-run the dlt pipeline. Closes once Phase 5's Dagster asset checks land (superseding the standalone `dbt source freshness` task previously planned here).

**Running under `SYSADMIN`, not scoped down (flagged July 2026):** broader than the job needs. A `CI_DEPLOYER` custom role (warehouse usage + schema-level create/write only) is a known follow-up, deprioritized behind the README/walkthrough and a baseball-question mart.

**Design decided for the above, not yet implemented (decided August 2026):** a two-database, two-role Snowflake dev/prod split — `RAYS_ANALYTICS_DEV` (broad-access `DEV_ROLE`) and `RAYS_ANALYTICS` (scoped `CI_DEPLOYER` role, CI-only). This is the standard Snowflake/dbt community pattern: separate database per environment plus separate role per environment, not a schema-only split like the current `RAW`/`DEV`/`PROD` schemas inside one database. Gives the already-tracked `CI_DEPLOYER` item a concrete shape; still no target implementation date.

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

#### Phase 4 — Ingestion (~1 week, slimmed for core path) ✅ COMPLETE

**Resolved June 2026:** dlt over Openflow — see Key Architectural Decisions. No longer a blocking pause.

**Core goal:** Replace `load_mlb_data.py` with a proper dlt pipeline writing directly into `RAYS_ANALYTICS.RAW`; add Statcast data via pybaseball; build staging models over dlt raw output; implement incremental loading. **No bronze/Iceberg layer in this pass.**

Full completed-items lists (June and July 2026 sessions): see CHANGELOG.md.

**Closed out:** CI dual-job architecture (Snowflake-on-merge) — `fix/ci-snowflake-key-pair-auth` (PR #26) merged 2026-07-20, adding the Snowflake CI job on key-pair auth. Last Phase 4 blocker resolved.

**Deferred, not blocking:**
- Scoping the CI job's Snowflake role down from `SYSADMIN` to a dedicated `CI_DEPLOYER` role (see CI Architecture Notes) — punted, no target phase
- **Next data source, TBD (decided August 2026):** Statcast/pybaseball is no longer the planned next data addition. Decision: it's not categorically more useful for this project than other sources worth exploring; no replacement has been chosen yet. Open for next session — don't assume Statcast by default going forward.

**Key notes:**
- Incremental loading needs a cursor column. `games` does NOT use `dlt.sources.incremental()` (see Key Architectural Decisions); whichever data source is chosen next (TBD as of August 2026 — see Deferred, above) will need the real cursor pattern.
- Deliberately introduce a schema change and observe dlt/dbt source freshness response — not yet done

**Bonus-track note (when revisited):** S3 + Iceberg + Snowflake Open Catalog bronze layer — dlt writes once to S3, Snowflake/DuckDB read from that location as separate engines. Setup: `ORGADMIN`-created Open Catalog account, S3 bucket, scoped IAM credentials. Single-writer discipline applies.

**Skills locked in (core):** Python-based ingestion, dlt resource/source/pipeline model, raw/staging layer pattern, merge write-disposition, destination-parameterized pipeline design, schema drift handling.

**Skills locked in (bonus, when revisited):** Iceberg format and REST catalog mechanics, S3/IAM setup, storage-layer portability, incremental loading with a real cursor.

---

#### Phase 5 — Orchestration and Observability (~6–9 hours, likely spanning multiple sessions) — CORE, re-scoped July 2026

**Core goal (revised August 2026):** Self-hosted Dagster OSS, on a small VPS via Docker Compose (see Orchestration Hosting decision in Key Architectural Decisions), replaces GitHub Actions cron as the production scheduler. GitHub Actions keeps its existing role as the PR/merge-time code-correctness gate; that doesn't change. **Note:** the DuckDB-build half of that gate is itself under revision — see the DuckDB-dropped-as-build-target decision and the CI/Makefile/profiles.yml follow-up flagged in Current Status.

**Scope:**
- Stand up the four-service Docker Compose stack on the VPS: `dagster-webserver`, `dagster-daemon`, a dedicated user-code gRPC server, and Postgres for run/event storage — plus a Tailscale sidecar so the webserver is reachable only via the tailnet, never a public port
- Wrap the existing dlt `games` pipeline as a Dagster asset
- Generate dbt model assets via `@dbt_assets` off `manifest.json` — one asset per dbt model, no DAG remodeling
- Freshness checks via Dagster asset checks (configurable from dbt `meta` config in `schema.yml`), replacing the standalone `dbt source freshness` task previously planned
- Alerting: email over Slack for a solo project — simpler, already reaches phone via Mail push, no new account/app to check. Elementary is no longer a Phase 5 dependency; Dagster's own asset checks + sensors cover the freshness-alerting use case natively. Elementary remains a possible separate future decision for dbt-test-specific anomaly detection/reporting beyond what Dagster gives.

**Known open item, not urgent:** even with Dagster running, there's currently no alerting for "run succeeded but data is wrong" (e.g., a clean run that pulled zero games, or stale/duplicate data) — only hard failures trigger a notification today (GitHub's default on-failure email). Requires actively writing freshness/volume/quality checks once Dagster is up; doesn't come for free with the migration.

**Bonus-track note (reworded August 2026):** dbt Projects on Snowflake remains bonus-track curiosity — worth exploring on its own terms as platform-depth learning, same framing as the other bonus-track items (Time Travel, Zero-Copy Cloning, Cortex, Marketplace, Streamlit). Not a fallback plan contingent on Dagster's success or failure; dbt Core stays the transformation tool and the Dagster hosting decision above is settled, not provisional.

**Skills locked in (core):** Asset-based orchestration (Dagster OSS), `dagster-dbt` asset generation from `manifest.json`, asset checks, self-hosted daemon process management via Docker Compose on a VPS, Tailscale sidecar networking, scheduled runs, failure alerting, data observability.

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

**Phase 4 complete.** Phase 5 orchestration decision made and re-scoped (Dagster OSS, self-hosted on a VPS via Docker Compose — hosting decision revised August 2026, supersedes the earlier Mac Mini/launchd plan) — implementation not yet started. A DuckDB-as-scratchpad-only decision (also August 2026) is likewise decided but not yet implemented in code/config.

**Next actions:**
1. Decide VPS provider/region/instance size (Hetzner discussed favorably on cost, not committed); stand up the four-service Docker Compose stack (`dagster-webserver`, `dagster-daemon`, user-code gRPC server, Postgres) plus the Tailscale sidecar
2. Wrap the `games` dlt pipeline as a Dagster asset; generate dbt model assets via `@dbt_assets` off `manifest.json`
3. Add Dagster asset checks for freshness (from dbt `meta` config) and email alerting
4. Decide the next data source to add — Statcast/pybaseball is no longer the assumed default (see Phase 4 Deferred); open question for next session
5. Phase 6: decide Lightdash vs. Metabase vs. keeping Cube+Evidence

**Deferred, no target phase:**
- Scoping the CI job's Snowflake role down from `SYSADMIN` to a dedicated `CI_DEPLOYER` role — design now decided (two-database, two-role split: `RAYS_ANALYTICS_DEV`/`DEV_ROLE` and `RAYS_ANALYTICS`/`CI_DEPLOYER`, see CI Architecture Notes), implementation still not started
- Updating `ci.yml`, `profiles.yml`, and the `Makefile` to match the DuckDB-dropped-as-build-target decision (see Key Architectural Decisions) — the current CI/Makefile/profiles.yml still describe the old DuckDB-build pattern

Full session-by-session history: see CHANGELOG.md.
