#!/usr/bin/env python3
"""
fetch_skills.py — How often is each tracked Skill/lib repo actually referenced
by public repos, plus social metadata.

Signals per repo (owner/name):
  - references (our "dependents" proxy):
      * libs  → GitHub code search total_count for
                "<repo-name>" filename:package.json OR filename:requirements.txt
                OR filename:pyproject.toml
      * skills → "<owner>/<name>" filename:mcp.json (agent configs reference
                the full path, e.g. "anthropics/skills")
  - stars / forks / pushed_at: REST /repos/{owner}/{name}

Why not GraphQL repositoriesDependentsCount? That field does not exist on the
GitHub GraphQL Repository type (verified: 'undefinedField'), and the web
used-by page is ToS-gray. Manifest-file search counts are the official,
reproducible replacement — same "behavioral evidence" spirit.

Rate limits: code search 30 req/min (authenticated) → sleep 2.2 s between
searches. REST meta: 5000 req/h — negligible for a handful of repos.
"""

from __future__ import annotations

import os, json, time, datetime
import urllib.request, urllib.parse
from pathlib import Path

TOKEN = os.environ.get("GH_PAT")
if not TOKEN:
    raise SystemExit("ERROR: GH_PAT env var not set.")

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR  = REPO_ROOT / "data" / "skills"
HISTORY   = sorted(DATA_DIR.glob("*.json"))[-4:]

import sys
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
from mcp_packages import SKILL_REPOS, AGENT_FRIENDLY_LIBS, MANIFEST_QUERY_BY_FULL_PATH

# Dedup, preserve order
ALL_REPOS = list(dict.fromkeys(SKILL_REPOS + AGENT_FRIENDLY_LIBS))

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "agent-called-what/0.1",
}

# Manifest files that signal "a repo depends on this project"
MANIFEST_OR = " OR ".join(
    f"filename:{m}" for m in ("package.json", "requirements.txt", "pyproject.toml")
)


def get_json(url: str, retries: int = 3) -> dict:
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < retries:
                wait = 30 * (attempt + 1)
                print(f"  ⚠️  HTTP {e.code} from {url} — retry {attempt + 1}/{retries} in {wait}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"GET {url} failed after {retries + 1} attempts")


def search_reference_count(query: str) -> int:
    """Return total_count for a GitHub code search query."""
    q = urllib.parse.quote(query)
    data = get_json(f"{API}/search/code?q={q}&per_page=1")
    return int(data.get("total_count", 0))


def repo_meta(owner: str, name: str) -> dict | None:
    try:
        d = get_json(f"{API}/repos/{owner}/{name}")
        return {
            "stars": d.get("stargazers_count", 0) or 0,
            "forks": d.get("forks_count", 0) or 0,
            "pushed_at": d.get("pushed_at", "") or "",
        }
    except Exception as e:
        print(f"  ⚠️  repo meta failed for {owner}/{name}: {e}")
        return None


def references_for(full: str) -> int:
    """Pick the right signal per repo type."""
    owner, name = full.split("/")
    if full in SKILL_REPOS:
        # Agent skills are wired into mcp.json / agent configs by full path
        return search_reference_count(f'"{full}" filename:mcp.json')
    if full in MANIFEST_QUERY_BY_FULL_PATH:
        # Generic short names ("ai", "serve", "dify") match noise in every
        # manifest (verified: '"ai" filename:package.json' ≈ 13M). The
        # owner-scoped path is a tiny but trustworthy signal instead.
        return search_reference_count(f'"{full}" {MANIFEST_OR}')
    return search_reference_count(f'"{name}" {MANIFEST_OR}')


def load_prev() -> dict:
    if not HISTORY:
        return {}
    with open(HISTORY[-1]) as f:
        return {row["repo"]: row for row in json.load(f)}


def main():
    today = datetime.date.today().isoformat()
    out_path = DATA_DIR / f"{today}.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prev = load_prev()

    rows = []
    total = len(ALL_REPOS)
    print(f"Scanning {total} repos: manifest references + social metadata…")

    for i, full in enumerate(ALL_REPOS, 1):
        owner, name = full.split("/")

        meta = repo_meta(owner, name)
        if meta is None:
            print(f"  [{i:2d}/{total}] {full:<40} ❌ skipped (repo not found / renamed?)")
            continue

        refs = references_for(full)

        prev_row = prev.get(full, {})
        is_new = full not in prev
        # Newly added repo: delta vs nothing is meaningless → 0 + newcomers flag.
        delta_stars = 0 if is_new else meta["stars"] - prev_row.get("stars", 0)
        delta_deps  = 0 if is_new else refs     - prev_row.get("dependents", 0)

        row = {
            "repo": full,
            "stars": meta["stars"],
            "forks": meta["forks"],
            "dependents": refs,
            "last_commit": meta["pushed_at"],
            "delta_stars": delta_stars,
            "delta_dependents": delta_deps,
            "is_new": is_new,
            "signal": "code-search manifest reference count",
        }
        rows.append(row)
        print(f"  [{i:2d}/{total}] {full:<40} ⭐{meta['stars']:>7}  refs={refs:>6}  Δs={delta_stars:+d}")

        # Code search cap: 10 req/min (verified for OAuth tokens) → 7 s spacing
        if i < total:
            time.sleep(7.0)

    rows.sort(key=lambda r: r["dependents"], reverse=True)

    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"\n✅ Wrote {out_path}  ({len(rows)} repos)")

if __name__ == "__main__":
    main()
