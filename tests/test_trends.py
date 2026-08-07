"""Tests for weekly trends computation (scripts/compose.py:build_trends).

Uses only stdlib `unittest` per AGENTS.md rule 5 (no new pip dependencies).
Run: python -m unittest tests.test_trends -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compose import build_trends  # noqa: E402


def mcp_rows():
    """Two entries with deltas; one brand-new entry."""
    return [
        {"package": "server-a", "call_count": 500, "weekly_delta": 40, "is_new": False},
        {"package": "server-b", "call_count": 100, "weekly_delta": -5, "is_new": False},
        {"package": "server-c", "call_count": 77, "weekly_delta": 0, "is_new": True},
    ]


def skill_rows():
    """One rising lib, one flat lib."""
    return [
        {"repo": "acme/lib", "dependents": 900, "delta_dependents": 120, "is_new": False},
        {"repo": "acme/old", "dependents": 300, "delta_dependents": 0, "is_new": False},
    ]


def ranked_tables():
    """Ranked view of the same names, so rank lookups resolve."""
    mcp_ranked = [
        {"package": "server-a", "rank": 1},
        {"package": "server-b", "rank": 2},
        {"package": "server-c", "rank": 3},
    ]
    skill_ranked = [
        {"repo": "acme/lib", "rank": 1},
        {"repo": "acme/old", "rank": 2},
    ]
    return mcp_ranked, skill_ranked


class TestBuildTrends(unittest.TestCase):

    def test_movers_positive_deltas_sorted_desc(self):
        mcp_r, skill_r = ranked_tables()
        t = build_trends(mcp_rows(), skill_rows(), mcp_r, skill_r)
        self.assertEqual([m["name"] for m in t["movers"]], ["acme/lib", "server-a"])
        self.assertEqual(t["movers"][0]["delta"], 120)
        self.assertEqual(t["movers"][1]["delta"], 40)

    def test_newcomers_excluded_from_movers(self):
        mcp_r, skill_r = ranked_tables()
        t = build_trends(mcp_rows(), skill_rows(), mcp_r, skill_r)
        names = [m["name"] for m in t["movers"]]
        self.assertNotIn("server-c", names)

    def test_declining_sorted_most_negative_first(self):
        mcp_r, skill_r = ranked_tables()
        t = build_trends(mcp_rows(), skill_rows(), mcp_r, skill_r)
        self.assertEqual([m["name"] for m in t["declining"]], ["server-b"])

    def test_newcomers_listed_with_table_and_value(self):
        mcp_r, skill_r = ranked_tables()
        t = build_trends(mcp_rows(), skill_rows(), mcp_r, skill_r)
        self.assertEqual(
            t["newcomers"],
            [{"table": "mcp_servers", "name": "server-c", "value": 77, "rank": 3}],
        )

    def test_trend_entries_carry_table_field_current_rank(self):
        mcp_r, skill_r = ranked_tables()
        t = build_trends(mcp_rows(), skill_rows(), mcp_r, skill_r)
        m = t["movers"][0]
        self.assertEqual(m["table"], "agent_skills")
        self.assertEqual(m["field"], "dependents")
        self.assertEqual(m["current"], 900)
        self.assertEqual(m["rank"], 1)

    def test_no_history_all_zero_deltas(self):
        # First run: no previous snapshot → deltas are all 0 → no movers/declining
        mcp_r = [{"package": "server-a", "rank": 1}]
        skill_r = [{"repo": "acme/lib", "rank": 1}]
        t = build_trends(
            [{"package": "server-a", "call_count": 5, "weekly_delta": 0, "is_new": False}],
            [{"repo": "acme/lib", "dependents": 5, "delta_dependents": 0, "is_new": False}],
            mcp_r, skill_r,
        )
        self.assertEqual(t["movers"], [])
        self.assertEqual(t["declining"], [])
        self.assertEqual(t["newcomers"], [])

    def test_movers_limited_to_top10(self):
        mcp_r = [{"package": f"s{i}", "rank": i} for i in range(1, 16)]
        rows = [
            {"package": f"s{i}", "call_count": 100, "weekly_delta": i, "is_new": False}
            for i in range(1, 16)
        ]
        t = build_trends(rows, [], mcp_r, [])
        self.assertEqual(len(t["movers"]), 10)
        self.assertEqual(t["movers"][0]["name"], "s15")


if __name__ == "__main__":
    unittest.main()
