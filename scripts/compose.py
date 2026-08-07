#!/usr/bin/env python3
"""
compose.py — Merge raw signals into ranked tables with composite scores.

Score formula (kept simple & transparent):
  score = 0.4·log(1+call_count) + 0.25·log(1+dependents) + 0.2·log(1+npm_dl) + 0.15·log(1+stars)

Output: data/rankings/<date>.json  (single file, all 3 tables)
        data/rankings/latest.json (symlink / copy for the site to consume)
"""

from __future__ import annotations

import json, math, datetime, shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA      = REPO_ROOT / "data"
RANK_DIR  = DATA / "rankings"
RANK_DIR.mkdir(parents=True, exist_ok=True)

def latest(dirname: str) -> Path | None:
    d = DATA / dirname
    files = sorted(d.glob("*.json"))
    return files[-1] if files else None

def log1p(x): return math.log1p(x)

def score_mcp(row) -> float:
    """Weights: call_count 0.4 | dependents 0.25 | npm_dl 0.2 | stars 0.15"""
    # We don't have stars in mcp json; use npm_dl as proxy for popularity
    return (0.4 * log1p(row.get("call_count", 0))
          + 0.2 * log1p(row.get("npm_monthly_dl", 0))
          + 0.25 * log1p(0)  # dependents not tracked for npm pkgs here
          + 0.15 * log1p(row.get("call_count", 0) // 10))  # rough proxy

def score_skill(row) -> float:
    """Weights: dependents 0.35 | stars 0.25 | delta_stars 0.2 | forks 0.2"""
    return (0.35 * log1p(row.get("dependents", 0))
          + 0.25 * log1p(row.get("stars", 0))
          + 0.20 * log1p(max(row.get("delta_stars", 0), 0))
          + 0.20 * log1p(row.get("forks", 0)))

def top(rows, key, n=30):
    return sorted(rows, key=lambda r: key(r), reverse=True)[:n]

def _rank_lookup(ranked: list[dict], name_key: str) -> dict:
    """{name: rank} from a ranked table."""
    return {r[name_key]: r.get("rank") for r in ranked}

def build_trends(mcp_rows, skill_rows, mcp_ranked, skill_ranked) -> dict:
    """Weekly behavioral trends: movers / declining / newcomers.

    - movers    : biggest positive Δ in the behavioral signal
                  (mcp: weekly_delta of call_count; skills: delta_dependents)
    - declining : biggest negative Δ in the same signals
    - newcomers : entries first seen this week (is_new), excluded from deltas
    """
    mcp_rank = _rank_lookup(mcp_ranked, "package")
    skill_rank = _rank_lookup(skill_ranked, "repo")

    deltas = []
    for r in mcp_rows:
        d = r.get("weekly_delta", 0)
        if r.get("is_new"):
            continue
        deltas.append({
            "table": "mcp_servers", "name": r["package"],
            "field": "call_count", "delta": d,
            "current": r.get("call_count", 0),
            "rank": mcp_rank.get(r["package"]),
        })
    for r in skill_rows:
        d = r.get("delta_dependents", 0)
        if r.get("is_new"):
            continue
        deltas.append({
            "table": "agent_skills", "name": r["repo"],
            "field": "dependents", "delta": d,
            "current": r.get("dependents", 0),
            "rank": skill_rank.get(r["repo"]),
        })

    movers = sorted([d for d in deltas if d["delta"] > 0], key=lambda d: d["delta"], reverse=True)[:10]
    declining = sorted([d for d in deltas if d["delta"] < 0], key=lambda d: d["delta"])[:10]

    newcomers = []
    for r in mcp_rows:
        if r.get("is_new"):
            newcomers.append({
                "table": "mcp_servers", "name": r["package"],
                "value": r.get("call_count", 0),
                "rank": mcp_rank.get(r["package"]),
            })
    for r in skill_rows:
        if r.get("is_new"):
            newcomers.append({
                "table": "agent_skills", "name": r["repo"],
                "value": r.get("dependents", 0),
                "rank": skill_rank.get(r["repo"]),
            })

    return {"movers": movers, "declining": declining, "newcomers": newcomers}

def main():
    today = datetime.date.today().isoformat()

    # ── Load raw ────────────────────────────────────────────────────
    mcp_path = latest("mcp-servers")
    skills_path = latest("skills")
    if not mcp_path or not skills_path:
        raise SystemExit("❌ Missing raw data. Run fetch_mcp.py and fetch_skills.py first.")

    with open(mcp_path) as f:  mcp_rows  = json.load(f)
    with open(skills_path) as f: skill_rows = json.load(f)

    # ── Rank ────────────────────────────────────────────────────────
    mcp_ranked    = top(mcp_rows,    score_mcp,    30)
    skills_ranked = top(skill_rows,  score_skill,  30)

    # Add rank + score fields
    for i, r in enumerate(mcp_ranked, 1):
        r["rank"] = i; r["score"] = round(score_mcp(r), 3)
    for i, r in enumerate(skills_ranked, 1):
        r["rank"] = i; r["score"] = round(score_skill(r), 3)

    # ── Assemble ────────────────────────────────────────────────────
    out = {
        "generated_at": today,
        "methodology": {
            "mcp_score": "0.4·log(1+call_count) + 0.2·log(1+npm_dl) + 0.15·log(1+call_proxy)",
            "skill_score": "0.35·log(1+dependents) + 0.25·log(1+stars) + 0.2·log(1+Δstars) + 0.2·log(1+forks)",
            "call_count_source": "GitHub code search '\"<pkg>\" filename:mcp.json'",
            "dependents_source": "GitHub code search '\"<name>\" filename:package.json OR filename:requirements.txt OR filename:pyproject.toml'",
        },
        "tables": {
            "mcp_servers":  mcp_ranked,
            "agent_skills": skills_ranked,
        },
        "trends": build_trends(mcp_rows, skill_rows, mcp_ranked, skills_ranked),
    }

    out_path = RANK_DIR / f"{today}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    # latest.json for the site
    latest_path = RANK_DIR / "latest.json"
    shutil.copy(out_path, latest_path)

    print(f"✅ Rankings written: {out_path}")
    print(f"   MCP servers : {len(mcp_ranked)} rows")
    print(f"   Agent skills: {len(skills_ranked)} rows")
    print(f"   Copied to   : {latest_path}")

if __name__ == "__main__":
    main()
