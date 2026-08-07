# agent-called-what

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Weekly Update](https://img.shields.io/badge/update-weekly-blue.svg)](.github/workflows/weekly.yml)
[![Site](https://img.shields.io/badge/site-GitHub%20Pages-8A2BE2)](https://zensoro.github.io/agent-called-what/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> What do AI agents actually call on GitHub? Not star-based — **behavior-based**.

Every other "AI agent ranking" is just a star counter with extra steps. This repo measures the thing that actually matters: **which MCP servers, agent skills, and libraries are being wired up and invoked by real agents in the wild**, inferred from public `mcp.json` configurations and repository dependency graphs.

## 📊 Live snapshot — 2026-08-07

The full dataset updates **every Monday** via GitHub Actions. Latest Top 5:

**🔌 MCP servers**

| # | Package | `mcp.json` call count | npm downloads/mo | Δ (week) | Score |
|---|---|---|---|---|---|
| 1 | `@modelcontextprotocol/server-filesystem` | 3,560 | 2,079,412 | 0 | 7.06 |
| 2 | `@modelcontextprotocol/server-github` | 2,536 | 563,482 | 0 | 6.61 |
| 3 | `@modelcontextprotocol/server-memory` | 1,832 | 407,394 | 0 | 6.37 |
| 4 | `@modelcontextprotocol/server-postgres` | 1,134 | 507,987 | 0 | 6.15 |
| 5 | `@modelcontextprotocol/server-puppeteer` | 538 | 129,255 | 0 | 5.47 |

**🧠 Agent skills & libraries**

| # | Repo | Dependents | Stars | Δ deps | Score |
|---|---|---|---|---|---|
| 1 | `langchain-ai/langchain` | 340,480 | 143,545 | 0 | 9.44 |
| 2 | `langchain-ai/langgraph` | 108,288 | 39,025 | 0 | 8.60 |
| 3 | `microsoft/autogen` | 66,688 | 60,265 | 0 | 8.46 |
| 4 | `agno-agi/agno` | 50,816 | 41,601 | 0 | 8.18 |
| 5 | `crewAIInc/crewAI` | 16,448 | 56,690 | 0 | 7.93 |

Trends start appearing from the second weekly update.

Full rankings (Top 30 MCP + all skills): [`data/rankings/latest.json`](data/rankings/latest.json) · [interactive site](https://zensoro.github.io/agent-called-what/)

## How it works

| Signal | Source | Method |
|---|---|---|
| **MCP server popularity** | Public `mcp.json` files on GitHub | GitHub code search: `"<pkg>" filename:mcp.json` → `total_count` |
| **Skill / lib used-by** | Public repos referencing it in manifests | GitHub code search: `"<name>" filename:package.json OR filename:requirements.txt OR filename:pyproject.toml` → `total_count` |
| **Download velocity** | npm registry | `api.npmjs.org/downloads/point/last-month/<pkg>` |

The composite score formula is documented in [`data/rankings/latest.json` → `methodology`](data/rankings/latest.json) and in [`site/methodology.md`](site/methodology.md).

## Quick start

```bash
# 1. Clone
git clone https://github.com/Zensoro/agent-called-what.git
cd agent-called-what

# 2. Set your GitHub token
cp .env.example .env
# edit .env and paste your GH_PAT (needs 'repo' + 'read:user' scopes)

# 3. Run
export $(cat .env | xargs)
python scripts/fetch_mcp.py        # ~6-9 min for 40 packages (10 req/min cap)
python scripts/fetch_skills.py     # ~2-3 min
python scripts/compose.py          # merges → data/rankings/latest.json
```

No dependencies beyond the Python stdlib. No API fees. Results are committed as versioned JSON.

## Project layout

```
agent-called-what/
├── data/
│   ├── mcp-servers/YYYY-MM-DD.json   # raw MCP call counts
│   ├── skills/YYYY-MM-DD.json       # raw skill/lib metadata
│   └── rankings/
│       ├── latest.json              # ← the site reads this
│       └── YYYY-MM-DD.json          # historical snapshot
├── scripts/
│   ├── lib/mcp_packages.py          # ← seed list (PR new entries here!)
│   ├── fetch_mcp.py
│   ├── fetch_skills.py
│   └── compose.py
├── site/                           # VitePress static site (GitHub Pages)
├── .github/workflows/weekly.yml    # auto-runs every Monday 02:00 UTC
└── README.md
```

## Why this is open source

Two reasons:

1. **Data should be forkable.** Every snapshot is a versioned JSON file in `data/`. Clone the repo, run `git log -- data/mcp-servers/`, and you have a time series. No API to hit, no rate limit, no "sign up for the pro tier."
2. **Methodology should be auditable.** If you think the weights are wrong, the queries are biased, or I missed a popular MCP server — open a PR. The whole pipeline is plain Python + stdlib.

## Contributing

- **New MCP server?** Add it to `scripts/lib/mcp_packages.py` → `MCP_PACKAGES` tuple list. Re-run `compose.py`.
- **Better scoring?** Open an issue explaining the change; we tweak weights in `scripts/compose.py`.
- **Bug?** File an issue with the traceback and your `GH_PAT` scopes (not the token itself!).

## FAQ

**Q: Isn't code search rate-limited?** Yes — 10 req/min for OAuth tokens. That's why `fetch_mcp.py` sleeps 7 s between requests; a full run of 40 packages takes ~6-9 min.

**Q: Why not use GraphQL `repositoriesDependentsCount` for used-by?** That field doesn't exist on the `Repository` type (verified `undefinedField`), and scraping `/network/dependents` is ToS-gray. We count manifest-file references via code search instead — same behavioral evidence, official API.

**Q: How is this different from AgentScout / Billboard?** They rank by stars. We rank by *behavioral evidence* — config-file presence and dependency edges. Stars measure hype; config presence measures adoption.

## License

MIT — see [LICENSE](LICENSE).
