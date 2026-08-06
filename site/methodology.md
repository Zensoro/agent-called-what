# Methodology — How `agent-called-what` measures AI behavior

## The problem with star-based rankings

Every existing "AI agent top N" list is a star counter. Stars measure **hype** — who tweeted about it, who got on Hacker News, who has the slickest README. They do **not** measure whether any agent, anywhere, has actually wired up and called that package.

A repo with 50,000 stars that no MCP config references is less "used by AI" than a 200-star MCP server that appears in 400 `mcp.json` files.

## Three behavioral signals

### Signal 1 — Config-file presence (MCP servers)

**Hypothesis:** If an MCP server is actually being used, it appears in someone's `mcp.json` (Cursor, Claude Code, Cline, Continue) — a config file that lives in their repo.

**Method:** GitHub code search:
```
"<package-name>" filename:mcp.json
```
The `total_count` from the response is our `call_count`. We try an exact filename filter first; if 0, we broaden to `"<pkg>" mcpServers` (any file containing the package inside an `mcpServers` block).

**Why this works:** These configs are checked into source control by real developers using real agents. It's the closest public proxy to "this server is in an agent's toolkit."

**Caveats:**
- Private repos are invisible — we systematically undercount enterprise adoption.
- Some users keep `mcp.json` local (gitignored) — also invisible.
- A single popular template repo (e.g., a "starter kit") can inflate one package's count. We do not currently de-duplicate by template; this is a known limitation.

### Signal 2 — Dependency graph (Skills & libs)

**Hypothesis:** If an agent skill or library is widely depended upon, it shows up in other repos' dependency graphs.

**Method:** GitHub code search (REST), counting how many public repos reference
the package inside a manifest file. We query with a filename OR-clause, e.g.:
```
"<package-name>" filename:package.json OR filename:requirements.txt OR filename:pyproject.toml
```
For agent-skill repos (e.g. `anthropics/skills`) we instead query
`"<owner>/<name>" filename:mcp.json`, since skills are wired into agent configs
by full path. The `total_count` from the response is our "dependents" proxy.

**Why not `repositoriesDependentsCount`?** That GraphQL field does not exist on
the `Repository` type — every query returns `undefinedField` (verified). The web
used-by page is ToS-gray. Manifest-file search counts are the official,
reproducible replacement — same behavioral-evidence spirit, and the same
mechanism we already use for MCP servers.

**Caveats:**
- Counts *all* references in public repos, not just agent-related ones. A lib that's also a general-purpose utility will be over-counted.
- A single popular template repo can inflate counts; we do not currently de-duplicate by template.

### Signal 3 — Download velocity (npm registry)

**Method:** `https://api.npmjs.org/downloads/point/last-month/<pkg>` — no auth needed.

**Why:** A package with 2M monthly downloads is plausibly being pulled by agent runtimes, even if not every download is agent-driven. It's a sanity-check signal, weighted lower than behavioral ones.

## Composite score

### MCP server score
```
score = 0.4 · log(1 + call_count)
       + 0.2 · log(1 + npm_monthly_dl)
       + 0.15 · log(1 + call_count // 10)   # rough "star proxy"
```
> Note: we don't have a direct star signal for npm packages in this table; the third term is a coarse proxy. Improvements welcome via PR.

### Skill / library score
```
score = 0.35 · log(1 + dependents)
       + 0.25 · log(1 + stars)
       + 0.20 · log(1 + max(delta_stars, 0))
       + 0.20 · log(1 + forks)
```

**Why log?** Raw counts have extreme skew (one package at 50k, rest in the hundreds). Log-compression keeps the long tail visible while still ranking the leaders clearly.

**Why these weights?** Subjective, based on which signal we trust most. `call_count` and `dependents` are behavioral → higher weight. `stars` and `forks` are social → lower weight. **All weights are tunable** — open an issue with your reasoning and we'll iterate.

## Update cadence

GitHub Actions runs `fetch_mcp.py` + `fetch_skills.py` + `compose.py` every **Monday 02:00 UTC**. Each run appends a dated JSON to `data/mcp-servers/`, `data/skills/`, and `data/rankings/`. `latest.json` is overwritten in place for the site to consume.

## Known limitations & future work

| Limitation | Possible fix |
|---|---|
| Code search sees only public repos | Acceptable; we are a public-data project |
| Search counts are repo-name based, not package-id based | Fine-grained `dependency:` search once it covers manifests broadly |
| Very generic repo names (`ai`, `serve`, `dify`) over-count | Maintained allowlist `MANIFEST_QUERY_BY_FULL_PATH` — those repos are queried as `"<owner>/<name>"` instead of the bare name |
| No de-duplication of template-influenced counts | Add repo-age + star-velocity filter |
| NPM-only (no PyPI download signal yet) | Add `https://pypistats.org/api/` in v0.2 |
| Skill list is curated, not discovered | Use code search `"from anthropics.skills"` to auto-discover |

## Reproducibility

Every script in `scripts/` is pure Python + standard library. Clone the repo, set `GH_PAT`, run the three scripts, and you'll reproduce our rankings bit-for-bit. No hidden services, no proprietary data, no "contact us for the full dataset."

---

*Last updated: 2026-08-06 — v0.1*
