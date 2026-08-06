# AGENTS.md — Instructions for AI coding agents

You are an AI agent contributing to **agent-called-what**, an open-source project that ranks MCP servers, agent skills, and libraries by *behavioral evidence* (config-file presence + dependency graphs), not stars.

## Repo layout

```
agent-called-what/
├── data/
│   ├── mcp-servers/YYYY-MM-DD.json   # raw MCP call counts (one file per run)
│   ├── skills/YYYY-MM-DD.json       # raw skill/lib metadata
│   └── rankings/
│       ├── latest.json              # ← site consumes this
│       └── YYYY-MM-DD.json          # historical snapshot
├── scripts/
│   ├── lib/mcp_packages.py          # SEED LIST — add new MCP packages here
│   ├── fetch_mcp.py                # GitHub code search, 9 req/min, sleeps 7.5s
│   ├── fetch_skills.py             # GitHub GraphQL, ~1 pt/query
│   └── compose.py                  # merges raw → rankings/latest.json
├── site/                           # VitePress / Nextra static site
├── .github/workflows/weekly.yml    # auto-runs every Monday 02:00 UTC
├── .env.example                    # copy to .env, fill GH_PAT
└── README.md
```

## How to run (local dev)

```bash
cp .env.example .env                # fill GH_PAT (repo + read:user scopes)
export $(cat .env | xargs)
python scripts/fetch_mcp.py         # ~4-6 min for 30 packages
python scripts/fetch_skills.py      # ~2 min
python scripts/compose.py           # → data/rankings/latest.json
```

## Rules (non-negotiable)

1. **Never commit `.env` or any secret.** `.gitignore` covers it; double-check with `git status` before every commit.
2. **Never use `--force` push or `push -f`.** Only fast-forward commits from the Actions bot are allowed.
3. **Never run `rm -rf` on the repo.** Data files in `data/` are versioned artifacts — do not bulk-delete.
4. **Respect rate limits.** `fetch_mcp.py` already sleeps 7.5 s. Do not parallelize or remove the sleep. If you hit a 403, stop and report — do not retry in a loop.
5. **Reproducibility over cleverness.** Use only Python stdlib + `urllib`. No new pip dependencies without explicit user approval.
6. **Methodology changes need an issue first.** Don't silently change the scoring formula in `compose.py`. Open an issue, discuss, then PR.
7. **Secrets stay local.** Never echo `$GH_PAT`, never log it, never include it in error messages. If a script fails, print the error type, not the token.

## Extending the seed list

To add a new MCP server: edit `scripts/lib/mcp_packages.py` → `MCP_PACKAGES` list.

Format: `("package-name", "registry", "category")`
- `registry`: `"npm"` | `"pypi"` | `"git"`
- `category`: one of `filesystem | database | devops | web | ai | memory | communication | productivity | cloud | social | fintech | observability`

After editing, re-run `compose.py`. The new package will appear in the next ranking.

## Updating the site

The site lives in `site/` (VitePress or Nextra — your choice). It reads `data/rankings/latest.json` as its data source. When `latest.json` changes, rebuild the site:

```bash
cd site && npm run build
```

## Commit conventions

Use Conventional Commits:
- `feat(data): add 5 new MCP servers to seed list`
- `fix(fetch): handle 404 from deleted repo in GraphQL`
- `chore(actions): bump Python to 3.12`
- `docs(methodology): clarify log-compression rationale`

## When you're stuck

- **Rate limited:** wait 60 s, retry once, then stop and ask the user.
- **GraphQL returns null repository:** the repo was deleted or renamed — remove it from the seed list and note it in the commit.
- **npm download API 404:** the package name is wrong or not on npm — fix the seed list.
- **Unsure about a methodology change:** open an issue, don't guess.

## What "done" looks like

A successful run produces:
- ✅ `data/mcp-servers/YYYY-MM-DD.json` — non-empty, valid JSON, N rows = len(MCP_PACKAGES)
- ✅ `data/skills/YYYY-MM-DD.json` — non-empty, valid JSON
- ✅ `data/rankings/latest.json` — contains `methodology` + `tables.mcp_servers` + `tables.agent_skills`
- ✅ No secrets in `git status`
- ✅ `python -c "import json; json.load(open('data/rankings/latest.json'))"` passes

If all five check out, you're done. Commit, push, and report the summary to the user.
