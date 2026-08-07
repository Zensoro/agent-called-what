"""更新 README.md / README.zh-CN.md 中的「实时快照」表格区块。

由 .github/workflows/weekly.yml 在数据更新后调用（仅当数据有变化时）。
零依赖（Python 标准库），就地替换两个 README 中从快照标题到下一节标题之间的内容。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOP_N = 5


def _fmt_int(v):
    return f"{int(v):,}"


def _mcp_table(rows):
    lines = ["| # | Package | `mcp.json` call count | npm downloads/mo | Score |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['rank']} | `{r['package']}` | {_fmt_int(r['call_count'])} | "
            f"{_fmt_int(r['npm_monthly_dl'])} | {r['score']:.2f} |"
        )
    return "\n".join(lines)


def _skill_table(rows):
    lines = ["| # | Repo | Dependents | Stars | Score |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | `{r['repo']}` | {_fmt_int(r['dependents'])} | "
            f"{_fmt_int(r['stars'])} | {r['score']:.2f} |"
        )
    return "\n".join(lines)


def _mcp_table_cn(rows):
    lines = ["| # | 包 | `mcp.json` 引用数 | npm 月下载 | 得分 |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['rank']} | `{r['package']}` | {_fmt_int(r['call_count'])} | "
            f"{_fmt_int(r['npm_monthly_dl'])} | {r['score']:.2f} |"
        )
    return "\n".join(lines)


def _skill_table_cn(rows):
    lines = ["| # | 仓库 | 依赖数 | Star | 得分 |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | `{r['repo']}` | {_fmt_int(r['dependents'])} | "
            f"{_fmt_int(r['stars'])} | {r['score']:.2f} |"
        )
    return "\n".join(lines)


def render_en(d):
    date = d["generated_at"]
    mcp = d["tables"]["mcp_servers"][:TOP_N]
    skills = d["tables"]["agent_skills"][:TOP_N]
    return (
        f"## 📊 Live snapshot — {date}\n\n"
        "The full dataset updates **every Monday** via GitHub Actions. Latest Top 5:\n\n"
        "**🔌 MCP servers**\n\n"
        f"{_mcp_table(mcp)}\n\n"
        "**🧠 Agent skills & libraries**\n\n"
        f"{_skill_table(skills)}\n\n"
        "Full rankings (Top 30 MCP + all skills): "
        "[`data/rankings/latest.json`](data/rankings/latest.json) · "
        "[interactive site](https://zensoro.github.io/agent-called-what/)\n\n"
    )


def render_cn(d):
    date = d["generated_at"]
    mcp = d["tables"]["mcp_servers"][:TOP_N]
    skills = d["tables"]["agent_skills"][:TOP_N]
    return (
        f"## 📊 最新快照 — {date}\n\n"
        "数据集每周一由 GitHub Actions 自动更新。当前 Top 5：\n\n"
        "**🔌 MCP 服务器**\n\n"
        f"{_mcp_table_cn(mcp)}\n\n"
        "**🧠 Agent Skill 与库**\n\n"
        f"{_skill_table_cn(skills)}\n\n"
        "完整榜单（MCP Top 30 + 全部 Skill）："
        "[`data/rankings/latest.json`](data/rankings/latest.json) · "
        "[在线站点](https://zensoro.github.io/agent-called-what/)\n\n"
    )


def replace_block(text, header_pattern, new_block):
    new_text, n = re.subn(header_pattern, lambda m: new_block, text, count=1)
    if n != 1:
        raise RuntimeError(f"快照区块未找到或匹配到 {n} 处，请检查 README 结构")
    return new_text


def main():
    data = json.loads((ROOT / "data/rankings/latest.json").read_text())
    en_path = ROOT / "README.md"
    cn_path = ROOT / "README.zh-CN.md"
    en = replace_block(
        en_path.read_text(),
        re.compile(r"## 📊 Live snapshot — .*?\n(?=## How it works)", re.S),
        render_en(data),
    )
    cn = replace_block(
        cn_path.read_text(),
        re.compile(r"## 📊 最新快照 — .*?\n(?=## 原理)", re.S),
        render_cn(data),
    )
    en_path.write_text(en)
    cn_path.write_text(cn)
    print("README snapshot tables updated")


if __name__ == "__main__":
    main()
