# PROMPT — Build `agent-called-what` (open source, no monetization)

You are executing a complete project build inside OpenCode. The project is an **open-source dataset + static site** that ranks what AI agents actually call on GitHub — based on **behavioral proxy signals**, NOT GitHub stars. It is the behavioral counterpart to star-based rankings like AgentScout / Billboard.

Repo name: **`agent-called-what`** (verify availability first; fallbacks: `ai-call-rank`, `agent-used-by`). Owner: the user running this prompt. License: **MIT**. Language: **bilingual Chinese + English** (README, site, comments, commit messages — all bilingual).

---

## 1. STACK & TOOLING (do not deviate without reason)

- **Language**: Python 3.12+ for all data scripts (fetch_*.py, compose.py). Use stdlib + `requests` + `python-dotenv`. No heavy frameworks.
- **Package manager**: `uv` if available, else `pip` with `requirements.txt`.
- **Static site**: VitePress (Vue-based, fast, great for tabular ranking pages, built-in i18n). Do NOT use Nextra / Docusaurus — keep it simple.
- **CI/CD**: GitHub Actions. Two workflows:
  1. `weekly.yml` — cron `0 0 * * 1` (every Monday 00:00 UTC), runs scripts, commits `data/`, pushes.
  2. `deploy.yml` — on push to `main`, builds VitePress and deploys to `gh-pages`.
- **Config**: `opencode.json` already exists in repo root with permissions set. Read it before touching bash.
- **Secrets**: `GH_PAT` (GitHub Personal Access Token, classic, `repo` + `read:user` scopes) stored in GitHub repo secrets and in local `.env` (never commit `.env`). `ANTHROPIC_API_KEY` is for OpenCode itself, not for the project.

---

## 2. DIRECTORY STRUCTURE (create exactly this)

```
agent-called-what/
├── opencode.json              # already exists
├── README.md                  # bilingual, see section 6
├── README.zh.md               # 中文版 README（README.md 里用链接指向它）
├── LICENSE                    # MIT
├── .env.example               # documents required env vars
├── requirements.txt
├── package.json               # only for VitePress scripts
├── docs/                      # VitePress source
│   ├── .vitepress/
│   │   └── config.js          # i18n: en + zh
│   ├── index.md               # English landing
│   ├── zh/
│   │   └── index.md           # 中文落地页
│   ├── methodology.md         # English methodology
│   ├── zh/methodology.md      # 中文方法论
│   ├── mcp.md                 # MCP Servers ranking page
│   ├── zh/mcp.md
│   ├── skills.md              # Agent Skills ranking page
│   ├── zh/skills.md
│   └── libs.md                # Agent-Friendly Libraries ranking page
├── scripts/
│   ├── fetch_mcp.py           # code-search "mcpServers" hits
│   ├── fetch_skills.py        # GraphQL: repos under anthropics/skills + dependentsCount
│   ├── fetch_libs.py          # npm download counts + GitHub dependents
│   ├── compose.py             # merge → data/*.json + Top-N tables
│   └── lib/
│       ├── github.py           # REST + GraphQL helpers, rate-limit aware
│       └── scoring.py          # composite score formula
├── data/                      # committed, one file per snapshot
│   ├── mcp/
│   │   └── YYYY-MM-DD.json
│   ├── skills/
│   └── libs/
├── .github/
│   └── workflows/
│       ├── weekly.yml
│       └── deploy.yml
└── AGENTS.md                  # notes for future AI agents touching this repo
```

---

## 3. DATA SOURCES & EXACT API USAGE

### 3.1 GitHub REST — code search (MCP signal)

Endpoint: `GET https://api.github.com/search/code`
- Header: `Authorization: Bearer $GH_PAT`, `Accept: application/vnd.github+json`
- Query: `q=mcpServers filename:mcp.json extension:json`
- **HARD RATE LIMIT: 9 requests/minute for code search** (this is the critical constraint).
- Pagination: up to 1000 results (10 pages × 100). For v0.1, the top-50 MCP server package names are hard-coded in `scripts/lib/mcp_packages.py` as a seed list (extract from npm: `@modelcontextprotocol/server-*`, `mcp-server-*`, plus known ones: `filesystem`, `github`, `postgres`, `sqlite`, `fetch`, `memory`, `puppeteer`, `brave-search`, `google-maps`, `slack`, `notion`, `docker`, `kubernetes`, `aws`, `gcp`, `azure`, `gitlab`, `jira`, `linear`, `sentry`, `datadog`, `grafana`, `openai`, `anthropic`, `mistral`, `ollama`, `vllm`, `redis`, `mongo`, `mysql`, `elasticsearch`, `kafka`, `rabbitmq`).
- For each package, run a targeted query: `q=mcpServers "package-name" filename:mcp.json` to get the hit count → that is the **call-frequency proxy**.
- **Sleep 7 seconds between requests** (9/min = 6.67s, use 7s to stay safe). Log every request with timestamp.
- Exclude forks: add `fork:false` to query. Exclude test/benchmark repos: post-filter by repo name containing `test`, `benchmark`, `example`, `demo`, `sandbox` → drop those rows.

### 3.2 GitHub GraphQL — repo metadata + dependentsCount

Endpoint: `https://api.github.com/graphql`, same `GH_PAT`.

Batch in a single query where possible (saves rate-limit points):

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    stargazerCount
    forkCount
    repositoriesDependentsCount
    updatedAt
    description
    homepageUrl
    url
  }
}
```

- For skills: iterate the list of known skill repos (seed list in `scripts/lib/skill_repos.py`, e.g. `anthropics/skills`, `data-analytics-skills`, `guizang-ppt-skill`, `openclaw`, plus any under `anthropics/` org).
- **IMPORTANT**: `repositoriesDependentsCount` returns a NUMBER only — it does NOT give the list of dependents. Do NOT try to scrape `/network/dependents` HTML (ToS grey area, see Red Lines). The count itself is the signal.
- Rate limit: GraphQL points budget is 5000 points/hour; each simple repo query ≈ 1 point. Batch up to ~50 repos per query using aliases to stay efficient.

### 3.3 npm download counts

Endpoint: `https://api.npmjs.org/downloads/point/last-month/<package>`
- No auth needed. Returns `{ downloads: N, package: "..." }`.
- Only query packages that look like npm packages (start with `@` or are single-names). Skip others.
- Rate limit: very generous, but add 1s sleep between calls to be polite.

### 3.4 Third-party directories (cursor.directory / MCP.so)

- For v0.1: **do NOT scrape**. Instead, manually curate a small `scripts/lib/curated_popular.json` with ~20 entries you can verify via `webfetch` at build time. Mark each entry with `"source": "curated"`.
- The methodology page must disclose this is a curated seed, not a live scrape.

---

## 4. COMPOSITE SCORING (scripts/lib/scoring.py)

For each item in each category, compute:

```
score = w1 * log10(1 + call_count)
      + w2 * log10(1 + dependents_count)
      + w3 * log10(1 + npm_downloads_last_month)
      + w4 * log10(1 + stars)
```

Default weights (tunable via env vars, document in methodology):
- `w1` (call_count) = 0.4 — primary signal, what AI actually calls
- `w2` (dependents)  = 0.25
- `w3` (npm_dl)      = 0.2
- `w4` (stars)       = 0.15 — downweighted precisely because everyone else ranks by stars

All signals are **log-scaled** so a 1M-star repo doesn't dominate a 5k-star repo 200× over. Normalize per-category to 0-100 for display.

Output `data/<category>/YYYY-MM-DD.json` with schema:
```json
{
  "generated_at": "2026-08-06T00:00:00Z",
  "category": "mcp",
  "weights": { "w1": 0.4, "w2": 0.25, "w3": 0.2, "w4": 0.15 },
  "items": [
    {
      "rank": 1,
      "name": "@modelcontextprotocol/server-filesystem",
      "repo": "modelcontextprotocol/servers",
      "url": "https://github.com/modelcontextprotocol/servers",
      "call_count": 1234,
      "dependents_count": 56,
      "npm_downloads_last_month": 89000,
      "stars": 12345,
      "score": 87.3,
      "weekly_delta": null
    }
  ]
}
```

`weekly_delta` = current_score − previous_snapshot_score (null for first run). Compute in `compose.py` by reading the most recent prior file in the same directory.

---

## 5. VITEPRESS SITE

- Use VitePress with the **i18n** setup (`themeConfig.locales` with `en` and `zh`).
- Landing page (`docs/index.md` + `docs/zh/index.md`): hero block, one-paragraph pitch, three big cards linking to /mcp, /skills, /libs, a "How it works" section, and a live-updating "Latest snapshot: YYYY-MM-DD" pulled from `data/` at build time via a Vite plugin or a small Node script (`scripts/gen-snapshot-import.mjs`) that writes `docs/.vitepress/snapshot.json` consumed by the pages.
- Each ranking page: a sortable HTML table (use a tiny client-side script or just markdown tables generated by `compose.py` → `docs/_data/mcp.md` partials). Show columns: Rank, Name, Repo, Call Count, Dependents, npm DL, Stars, Score, Δ.
- Methodology page: fully explain signals, weights, exclusions, known biases, ToS stance. Be **honest about limitations** — that is the project's credibility.
- Site must build successfully with `npm run build` (output to `docs/.vitepress/dist`).

---

## 6. README (bilingual)

`README.md` (English, with a prominent link to `README.zh.md` at the top):
- **Title**: "What Do AI Agents Actually Call? — A behavior-based ranking of MCP servers, agent skills, and libraries on GitHub."
- **One-paragraph why**: star rankings are gamed and don't reflect agent behavior. This project measures what agents are actually configured to invoke.
- **Three big badges**: latest snapshot date, total items tracked, license MIT.
- **Quick links**: Methodology · MCP Rank · Skills Rank · Libs Rank · Live Site.
- **How to reproduce**: `cp .env.example .env`, fill `GH_PAT`, `pip install -r requirements.txt`, `python scripts/compose.py`.
- **How the weekly cron works** (one paragraph).
- **Contributing**: how to add a new MCP package / skill repo to the seed lists (PR → edit `scripts/lib/mcp_packages.py` or `skill_repos.py`).
- **License & attribution**.

`README.zh.md` (中文版): same structure, Chinese copy. Title: "AI Agent 到底在调什么？—— 基于行为信号的 GitHub MCP / Skills / 库排名。"

---

## 7. GITHUB ACTIONS

### `weekly.yml`
- Triggers: `schedule: - cron: '0 0 * * 1'` (Mondays) + `workflow_dispatch` (manual button).
- Permissions: `contents: write` (to commit data), `pages: write`, `id-token: write`.
- Steps: checkout (full, not shallow — needed for `git log` on data files), `actions/setup-python@v5` 3.12, `pip install -r requirements.txt`, `python scripts/compose.py`, `git config user.name "agent-called-what[bot]"`, `git config user.email "bot@users.noreply.github.com"`, `git add data/`, `git commit -m "chore(data): weekly snapshot $(date -u +%F)"` (only if changes), `git push`.
- **Critical**: set `GH_PAT` from `secrets.GH_PAT`. The GITHUB_TOKEN is NOT enough for the Search API's higher quotas — you need the PAT. Document this in `.env.example` and in the workflow comments.

### `deploy.yml`
- Triggers: push to `main` (including the weekly commit).
- Builds VitePress and deploys to `gh-pages` using `actions/deploy-pages@v4` + `actions/configure-pages@v4`. Standard VitePress deploy recipe.

---

## 8. RED LINES — things you MUST NOT do

1. **Do NOT scrape GitHub HTML** (`/network/dependents`, user profiles, etc.). GraphQL gives counts; lists are off-limits. Respect GitHub ToS.
2. **Do NOT `rm -rf` anything outside the repo.** The opencode.json already denies `rm -rf /` and `rm -rf ~`; do not try to override.
3. **Do NOT `git push --force` or `git push -f`** — denied in config.
4. **Do NOT commit `.env`, any `*token*`, `*secret*`, `*key*`, `*credential*` files.** opencode.json denies read on `*.env`; respect that and double-check with `git status` before any commit.
5. **Do NOT exceed 9 req/min on code search.** Sleep 7s minimum. If a run is interrupted, it is fine to re-run — the script should be idempotent.
6. **Do NOT hardcode the PAT** in any script. Read from `os.environ["GH_PAT"]` only.
7. **Do NOT invent data.** If an API call fails, log it and skip; do not fabricate numbers. Methodology page must list any missing/incomplete entries.
8. **Do NOT install unverified npm packages** globally. Use `npm install --save-dev` in the `docs/` context only.

---

## 9. DELIVERABLES CHECKLIST (verify before declaring done)

- [ ] Repo initialized, `opencode.json` present, `.env.example` documents `GH_PAT`.
- [ ] `requirements.txt` with `requests`, `python-dotenv`. `package.json` for VitePress.
- [ ] `scripts/lib/github.py` — REST + GraphQL helpers, rate-limit safe, 7s sleep on code search.
- [ ] `scripts/lib/scoring.py` — composite score with log scaling + normalization.
- [ ] `scripts/fetch_mcp.py` — produces intermediate `data/mcp/raw-YYYY-MM-DD.json`.
- [ ] `scripts/fetch_skills.py` — produces `data/skills/raw-*.json`.
- [ ] `scripts/fetch_libs.py` — produces `data/libs/raw-*.json`.
- [ ] `scripts/compose.py` — merges raw → final `data/<cat>/YYYY-MM-DD.json` with ranks + weekly_delta, also writes markdown table partials to `docs/_data/`.
- [ ] At least ONE successful full run: `python scripts/compose.py` completes end-to-end and produces 3 JSON files with real data (if `GH_PAT` is set; if not, generate with a `--demo` flag using mocked data so the pipeline is verifiable).
- [ ] VitePress site builds: `npm run build` exits 0, `docs/.vitepress/dist` populated.
- [ ] All six content pages present (en+zh × {landing, mcp, skills, libs, methodology} = 10 pages; landing and methodology are the critical ones, ranking pages can be 3 en + 3 zh).
- [ ] `README.md` + `README.zh.md` written, bilingual, with badges, methodology link, repro steps.
- [ ] `.github/workflows/weekly.yml` and `deploy.yml` created and syntactically valid (`actionlint` clean if available).
- [ ] `LICENSE` (MIT) present.
- [ ] `AGENTS.md` written — explains to future AI agents how this repo works, where the seed lists live, and the red lines.

---

## 10. COMMUNICATION STYLE

- Commit messages: bilingual, Conventional Commits style (`feat(data): ...`, `chore(ci): ...`). English primary, Chinese in parentheses when useful.
- In-code comments: English for public APIs, Chinese allowed for tricky logic.
- User-facing copy (site, README): fully bilingual.
- When you hit a rate limit or API error, **log it, skip, continue** — never abort the whole run for one failure.

---

## 11. LAUNCH PLAN (do not execute — leave as a markdown file for the user)

Create `LAUNCH.md` (bilingual) containing:
- HN submission title + body (English): "Show HN: I built a behavior-based ranking of what AI agents actually call on GitHub (not star-based)"
- r/LocalLlama cross-post (English).
- 即刻 / 掘金 / V2EX posts (中文): title + 3-paragraph body.
- Tweet / X thread outline (English, 5 tweets).
- Suggested launch day: a Monday, right after the first weekly cron run lands, so the "Latest snapshot" badge is fresh.

---

## 12. WHEN YOU FINISH

1. Run the full pipeline at least once end-to-end (with `--demo` if no PAT).
2. Run `npm run build` and confirm it exits 0.
3. `git status` — confirm nothing sensitive is staged.
4. Print a final summary to the user: file count, lines of code, sample Top-5 from each category, any warnings/errors encountered, and the exact next manual step (e.g. "create GitHub repo, push, add GH_PAT secret, enable GitHub Pages").

Begin. Read `opencode.json` first. Then plan with the TodoWrite tool, and execute.
