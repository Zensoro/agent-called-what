#!/usr/bin/env python3
"""
fetch_mcp.py — Count how often each MCP server appears in public mcp.json files.

Strategy: GitHub code search "mcpServers" filtered to filename:mcp.json.
For each known package, run a targeted query "<pkg-name> filename:mcp.json"
and record the `total_count`.

Rate limit: GitHub Search code = 9 req/min for authenticated requests.
We sleep 7.5 s between requests to stay safely under the limit.
"""

import os, json, time, datetime, statistics
from pathlib import Path
import urllib.request, urllib.parse

# ── Config ──────────────────────────────────────────────────────────
TOKEN = os.environ.get("GH_PAT")
if not TOKEN:
    raise SystemExit("ERROR: GH_PAT env var not set. Get a token at https://github.com/settings/tokens (needs 'repo' scope)")

SLEEP_SEC = 7.0          # 10 req/min cap (verified for OAuth tokens) → ~8.5/min
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data" / "mcp-servers"
HISTORY   = sorted(DATA_DIR.glob("*.json"))[-4:]   # last 4 snapshots for Δ

# Import seed list
import sys
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
from mcp_packages import MCP_PACKAGES

# ── GitHub Search helper ────────────────────────────────────────────
def search_code_count(query: str) -> int:
    """Return total_count for a GitHub code search query."""
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/code?q={q}&per_page=1"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agent-called-what/0.1",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise SystemExit("\n❌ 403 from code search — rate limited. Wait ~60 s and re-run. "
                             "Never retry in a tight loop.")
        raise
    # Abuse-rate-limit: check headers
    remaining = r.headers.get("X-RateLimit-Remaining")
    reset = r.headers.get("X-RateLimit-Reset")
    if remaining and int(remaining) < 2:
        print(f"  ⚠️  Rate limit nearly exhausted (remaining={remaining}, reset={reset}). Sleeping 60s.")
        time.sleep(60)
    return data.get("total_count", 0)

# ── NPM download helper (no auth needed) ──────────────────────────
def npm_monthly_downloads(pkg: str) -> int:
    """Fetch last-month download count from npm registry."""
    # Scoped packages must be URL-encoded in full (@scope%2Fpkg),
    # not truncated — otherwise we query a different/nonexistent name.
    name = urllib.parse.quote(pkg, safe="")
    url = f"https://api.npmjs.org/downloads/point/last-month/{name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"agent-called-what/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("downloads", 0)
    except Exception as e:
        print(f"  ⚠️  npm fetch failed for {pkg}: {e}")
        return 0

# ── Previous snapshot for Δ ────────────────────────────────────────
def load_prev() -> dict:
    if not HISTORY:
        return {}
    with open(HISTORY[-1]) as f:
        return {row["package"]: row for row in json.load(f)}

# ── Main ────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today().isoformat()
    out_path = DATA_DIR / f"{today}.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prev = load_prev()

    rows = []
    total = len(MCP_PACKAGES)
    print(f"Scanning {total} MCP packages via GitHub code search (9/min cap)…")
    print(f"ETA: ~{total * SLEEP_SEC / 60:.1f} min\n")

    for i, (pkg, registry, category) in enumerate(MCP_PACKAGES, 1):
        # Targeted query: package name inside mcp.json files
        query = f'"{pkg}" filename:mcp.json'
        count = search_code_count(query)
        # Fallback: if 0, try broader query without filename filter.
        # Must sleep BEFORE the fallback too — the 10/min cap counts
        # every search request, not just the primary ones.
        if count == 0:
            time.sleep(SLEEP_SEC)
            count = search_code_count(f'"{pkg}" mcpServers')

        # NPM downloads (only meaningful for npm packages)
        dl = npm_monthly_downloads(pkg) if registry == "npm" else 0

        prev_row = prev.get(pkg, {})
        is_new = pkg not in prev
        # Newly added seed package: its "delta" vs nothing is meaningless,
        # so we record 0 and mark it for the newcomers list instead.
        prev_count = prev_row.get("call_count", 0) if not is_new else 0
        delta = 0 if is_new else count - prev_count

        row = {
            "package": pkg,
            "registry": registry,
            "category": category,
            "call_count": count,
            "npm_monthly_dl": dl,
            "weekly_delta": delta,
            "is_new": is_new,
        }
        rows.append(row)
        print(f"  [{i:2d}/{total}] {pkg:<45} calls={count:>5}  npm_dl={dl:>8}  Δ={delta:+d}")

        # Throttle — respect 9 req/min for code search
        if i < total:
            time.sleep(SLEEP_SEC)

    # Sort by call_count desc
    rows.sort(key=lambda r: r["call_count"], reverse=True)

    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"\n✅ Wrote {out_path}  ({len(rows)} packages)")

if __name__ == "__main__":
    main()
