# agent-called-what

> What do AI agents actually call on GitHub? Not star-based — **behavior-based**.

Every other "AI agent ranking" is just a star counter with extra steps. This repo measures the thing that actually matters: **which MCP servers, agent skills, and libraries are being wired up and invoked by real agents in the wild**, inferred from public `mcp.json` configurations and repository dependency graphs.

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
├── site/                           # VitePress / Nextra static site
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
