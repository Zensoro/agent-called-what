---
title: Contributing
---

# Contributing to agent-called-what

Thanks for considering it — this project lives or dies by community input.

## Ways to help

### 1. Add a missing MCP server

Edit `scripts/lib/mcp_packages.py`. Add a tuple to `MCP_PACKAGES`:

```python
("mcp-server-notion", "pypi", "productivity"),
```

Format: `(package_name, registry, category)`

- `registry`: `"npm"` | `"pypi"` | `"git"`
- `category`: one of `filesystem | database | devops | web | ai | memory | communication | productivity | cloud | social | fintech | observability`

Commit convention: `feat(data): add mcp-server-notion to seed list`

### 2. Improve the scoring formula

Open an **issue first** explaining your reasoning. What signal are we under/over-weighting? What real-world behavior does your change better capture? Once discussed, submit a PR against `scripts/compose.py`.

### 3. Fix a bug

Check [open issues](https://github.com/Zensoro/agent-called-what/issues). Look for the `good first issue` label. Include a failing test or a clear repro in the PR description.

### 4. Extend the methodology

Got a new signal source? (e.g., PyPI download stats, GitHub Archive BigQuery, MCP.so directory scrape) Open an RFC-style issue. We want the methodology to evolve, but never silently.

## Development setup

```bash
git clone https://github.com/Zensoro/agent-called-what.git
cd agent-called-what
cp .env.example .env          # paste your GH_PAT
export $(cat .env | xargs)

python scripts/fetch_mcp.py
python scripts/fetch_skills.py
python scripts/compose.py

cd site && npm install && npm run dev   # preview site locally
```

## Rules

- **No `rm -rf`, no `--force` push, no secrets in commits.** The CI checks for `.env` but don't rely on it.
- **No new pip dependencies without discussion.** Stdlib only by default.
- **Reproducibility > cleverness.** If your change makes the pipeline require a new service or key, it needs a really good reason.
- **Methodology changes need an issue first.** Don't PR a weight tweak without explaining *why* in an issue.

## Code of Conduct

Be kind. Disagree on the weights, not on the person. We're all trying to make AI tooling more legible.
