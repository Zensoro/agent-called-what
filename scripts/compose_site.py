#!/usr/bin/env python3
"""
compose_site.py — Generate the actual Markdown tables for site/mcp.md and site/skills.md
from data/rankings/latest.json. Run after compose.py.
"""

import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANK = ROOT / "data" / "rankings" / "latest.json"
SITE  = ROOT / "site"

def fmt_int(n): return f"{n:,}" if isinstance(n, int) else str(n)
def fmt_delta(n):
    if not isinstance(n, int): return str(n)
    return f"+{n:,}" if n > 0 else f"{n:,}"

def gen_mcp_md(data: dict) -> str:
    today = data.get("generated_at", datetime.date.today().isoformat())
    rows = data["tables"].get("mcp_servers", [])
    body = f"---\ntitle: MCP Servers Ranking\n---\n\n# 🔌 MCP Servers — Behavior-Based Ranking\n\n_Updated: {today}_\n\n"
    body += (
        "## How to read this table\n\n"
        "| Column | Meaning |\n|---|---|\n"
        "| **Call Count** | Public `mcp.json` files on GitHub referencing this package |\n"
        "| **npm DL/mo** | Last-month download count from npm registry |\n"
        "| **Δ (week)** | Change in call count vs. previous snapshot |\n"
        "| **Score** | Composite: `0.4·log(1+calls) + 0.2·log(1+dl) + 0.15·log(1+call_proxy)` |\n\n"
        "## Top 30\n\n"
        "| # | Package | Registry | Category | Call Count | npm DL/mo | Δ (week) | Score |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    for r in rows[:30]:
        body += (
            f"| {r['rank']} | `{r['package']}` | {r.get('registry','')} "
            f"| {r.get('category','')} | {fmt_int(r.get('call_count',0))} "
            f"| {fmt_int(r.get('npm_monthly_dl',0))} | {fmt_delta(r.get('weekly_delta',0))} "
            f"| {r.get('score',0):.3f} |\n"
        )
    body += "\n---\n\n[← Home](./) · [Methodology](./methodology) · [Agent Skills](./skills)\n"
    return body

def gen_skills_md(data: dict) -> str:
    today = data.get("generated_at", datetime.date.today().isoformat())
    rows = data["tables"].get("agent_skills", [])
    body = f"---\ntitle: Agent Skills & Libraries Ranking\n---\n\n# 🧩 Agent Skills & Libraries — Behavior-Based Ranking\n\n_Updated: {today}_\n\n"
    body += (
        "## How to read this table\n\n"
        "| Column | Meaning |\n|---|---|\n"
        "| **Used-By** | Code-search manifest references: `\"<name>\" filename:package.json OR filename:requirements.txt OR filename:pyproject.toml` |\n"
        "| **Stars** | `stargazerCount` |\n"
        "| **Δ Stars** | Change since previous snapshot |\n"
        "| **Score** | `0.35·log(1+deps) + 0.25·log(1+stars) + 0.2·log(1+Δstars) + 0.2·log(1+forks)` |\n\n"
        "## Top 30\n\n"
        "| # | Repo | Used-By | Stars | Forks | Δ Stars | Score |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    for r in rows[:30]:
        body += (
            f"| {r['rank']} | [{r['repo']}](https://github.com/{r['repo']}) "
            f"| {fmt_int(r.get('dependents',0))} | {fmt_int(r.get('stars',0))} "
            f"| {fmt_int(r.get('forks',0))} | {fmt_delta(r.get('delta_stars',0))} "
            f"| {r.get('score',0):.3f} |\n"
        )
    body += "\n---\n\n[← Home](./) · [Methodology](./methodology) · [MCP Servers](./mcp)\n"
    return body

def main():
    if not RANK.exists():
        raise SystemExit("❌ data/rankings/latest.json not found. Run scripts/compose.py first.")
    data = json.loads(RANK.read_text())
    (SITE / "mcp.md").write_text(gen_mcp_md(data))
    (SITE / "skills.md").write_text(gen_skills_md(data))
    print(f"✅ Wrote {SITE/'mcp.md'}  ({len(data['tables'].get('mcp_servers',[]))} rows)")
    print(f"✅ Wrote {SITE/'skills.md'}  ({len(data['tables'].get('agent_skills',[]))} rows)")

if __name__ == "__main__":
    main()
