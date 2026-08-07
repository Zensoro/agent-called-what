#!/usr/bin/env python3
"""
check.py — Validate pipeline outputs before commit (CI gate + local sanity).

Enforces the "What done looks like" contract from AGENTS.md:
  1. data/mcp-servers/<latest>.json  — non-empty, valid JSON,
     row count == len(MCP_PACKAGES)
  2. data/skills/<latest>.json        — non-empty, valid JSON
  3. data/rankings/latest.json        — has `methodology`, `tables.mcp_servers`,
     `tables.agent_skills`
  4. No secrets in tracked files      — `.env` not tracked; no `GH_PAT=<token>`
     outside `.env.example` / workflow placeholders
  5. JSON round-trip passes

Exit 0 = ready to commit. Non-zero = fix something before committing.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data"
RANK_DIR = DATA / "rankings"

# Exclude: the .env.example template, the Actions workflow, and this file
# itself (its docstring documents the pattern `GH_PAT=<token>`).
SKIP_FOR_SECRET = {
    REPO_ROOT / ".env.example",
    REPO_ROOT / ".github" / "workflows" / "weekly.yml",
    REPO_ROOT / "scripts" / "check.py",
}
SECRET_RE = re.compile(r"GH_PAT\s*=\s*([^$\s][^\s]*)")

failures: list[str] = []


def latest(dirname: str) -> Path | None:
    d = DATA / dirname
    files = sorted(d.glob("*.json"))
    return files[-1] if files else None


def check(ok: bool, msg: str) -> None:
    status = "✅" if ok else "❌"
    print(f"{status} {msg}")
    if not ok:
        failures.append(msg)


def check_json_valid(path: Path) -> object | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        check(False, f"{path.name}: invalid JSON ({e})")
        return None


def check_secrets() -> None:
    # 4a. .env must not be tracked by git
    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.splitlines()
    except Exception:
        tracked = [str(p.relative_to(REPO_ROOT)) for p in REPO_ROOT.rglob("*")
                   if p.is_file() and "node_modules" not in p.parts and ".git" not in p.parts]
    check(".env" not in tracked, "`.env` must not be tracked by git")

    # 4b. No token-looking values in tracked content
    leak = []
    for rel in tracked:
        if rel.startswith(".github/") or rel.startswith("site/node_modules/"):
            continue
        p = REPO_ROOT / rel
        if not p.is_file() or p.suffix not in (".py", ".json", ".yml", ".yaml", ".md", ".sh", ".toml"):
            continue
        if p in SKIP_FOR_SECRET:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for m in SECRET_RE.finditer(text):
            # ${{ secrets.GH_PAT }} → starts with '{' → placeholder, skip
            if m.group(1).startswith("{"):
                continue
            leak.append(f"{rel}:{m.group(1)[:12]}…")
    check(not leak, "no GH_PAT=token in tracked files" + (f" — found in {leak}" if leak else ""))


def main() -> None:
    print("agent-called-what data validation\n")

    # 1. MCP raw snapshot
    mcp = latest("mcp-servers")
    check(mcp is not None, "data/mcp-servers/ has at least one snapshot")
    if mcp:
        rows = check_json_valid(mcp)
        if rows is not None:
            import sys as _sys
            _sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
            from mcp_packages import MCP_PACKAGES
            check(len(rows) == len(MCP_PACKAGES),
                  f"{mcp.name}: {len(rows)} rows == {len(MCP_PACKAGES)} seed packages")
            check(len(rows) > 0, f"{mcp.name}: non-empty")

    # 2. Skills raw snapshot
    sk = latest("skills")
    check(sk is not None, "data/skills/ has at least one snapshot")
    if sk:
        rows = check_json_valid(sk)
        if rows is not None:
            check(len(rows) > 0, f"{sk.name}: non-empty")

    # 3. Rankings
    rank = RANK_DIR / "latest.json"
    check(rank.exists(), "data/rankings/latest.json exists")
    if rank.exists():
        d = check_json_valid(rank)
        if isinstance(d, dict):
            check("methodology" in d, "latest.json has `methodology`")
            tables = d.get("tables", {})
            check(isinstance(tables.get("mcp_servers"), list) and len(tables["mcp_servers"]) > 0,
                  "latest.json has non-empty `tables.mcp_servers`")
            check(isinstance(tables.get("agent_skills"), list) and len(tables["agent_skills"]) > 0,
                  "latest.json has non-empty `tables.agent_skills`")
            for tbl in ("mcp_servers", "agent_skills"):
                rows_tbl = tables.get(tbl, [])
                ok_rows = all(isinstance(r, dict) and "rank" in r and "score" in r
                              for r in rows_tbl)
                check(ok_rows, f"every {tbl} row has rank+score ({len(rows_tbl)} rows)")

            trends = d.get("trends", {})
            check("trends" in d, "latest.json has `trends`")
            if isinstance(trends, dict):
                for key in ("movers", "declining", "newcomers"):
                    check(isinstance(trends.get(key), list),
                          f"trends.{key} is a list")
                ok_entry = all(
                    isinstance(e, dict)
                    and e.get("table") in ("mcp_servers", "agent_skills")
                    and "name" in e
                    for e in trends.get("movers", [])
                )
                check(ok_entry, f"every trends.movers entry has table+name ({len(trends.get('movers', []))} entries)")

    # 4. Secrets
    check_secrets()

    # 5. Round-trip (already implied by 1-3; explicit for the contract)
    if rank.exists():
        try:
            json.dumps(json.loads(rank.read_text()))
            check(True, "latest.json round-trips through json.dumps")
        except Exception as e:
            check(False, f"latest.json round-trip failed ({e})")

    print()
    if failures:
        print(f"✗ {len(failures)} check(s) failed — fix before committing.")
        sys.exit(1)
    print("✓ All checks passed — data is ready to commit.")


if __name__ == "__main__":
    main()
