# agent-called-what

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Weekly Update](https://img.shields.io/badge/update-weekly-blue.svg)](.github/workflows/weekly.yml)
[![Site](https://img.shields.io/badge/site-GitHub%20Pages-8A2BE2)](https://zensoro.github.io/agent-called-what/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> AI 在 GitHub 上到底调了什么？不是 star 榜，**是行为榜**。

市面上所有"AI Agent 排行榜"本质都是 star 计数器套壳。本仓库衡量的是真正重要的事：**真实的 AI Agent 在野外实际接入、调用了哪些 MCP Server、Skill 和库**——证据来自公开的 `mcp.json` 配置文件和仓库依赖图。

## 📊 最新快照 — 2026-09-07

数据集每周一由 GitHub Actions 自动更新。当前 Top 5：

**🔌 MCP 服务器**

| # | 包 | `mcp.json` 引用数 | npm 月下载 | Δ（周） | 得分 |
|---|---|---|---|---|---|
| 1 | `@modelcontextprotocol/server-filesystem` | 3,704 | 2,827,451 | +3,572 | 7.14 |
| 2 | `@modelcontextprotocol/server-github` | 2,552 | 444,016 | +2,445 | 6.57 |
| 3 | `@modelcontextprotocol/server-memory` | 1,766 | 405,883 | +1,662 | 6.35 |
| 4 | `@modelcontextprotocol/server-postgres` | 1,254 | 387,342 | +1,151 | 6.15 |
| 5 | `@modelcontextprotocol/server-puppeteer` | 522 | 108,298 | +495 | 5.42 |

**🧠 Agent Skill 与库**

| # | 仓库 | 依赖数 | Star | Δ 依赖 | 得分 |
|---|---|---|---|---|---|
| 1 | `langchain-ai/langchain` | 353,792 | 145,835 | +344,640 | 10.71 |
| 2 | `langchain-ai/langgraph` | 123,392 | 41,156 | +119,000 | 9.73 |
| 3 | `microsoft/autogen` | 66,688 | 60,846 | +64,276 | 9.45 |
| 4 | `agno-agi/agno` | 60,672 | 42,077 | +55,288 | 9.18 |
| 5 | `crewAIInc/crewAI` | 17,952 | 58,178 | +17,476 | 9.13 |

**📈 本周涨幅最高：** `langchain-ai/langchain`（dependents +344,640）。

完整榜单（MCP Top 30 + 全部 Skill）：[`data/rankings/latest.json`](data/rankings/latest.json) · [在线站点](https://zensoro.github.io/agent-called-what/)

## 原理

| 信号 | 来源 | 方法 |
|---|---|---|
| **MCP 服务器流行度** | GitHub 公开 `mcp.json` | 代码搜索 `"<pkg>" filename:mcp.json` 的 `total_count` |
| **Skill / 库 used-by** | 公开仓库清单文件引用 | GitHub code search `"<name>" filename:package.json OR filename:requirements.txt OR filename:pyproject.toml` 的 `total_count` |
| **下载增速** | npm 注册表 | `api.npmjs.org/downloads/point/last-month/<pkg>` |

复合打分公式见 `data/rankings/latest.json` 的 `methodology` 字段与 `site/methodology.md`。

## 快速开始

```bash
git clone https://github.com/Zensoro/agent-called-what.git
cd agent-called-what
cp .env.example .env          # 填入你的 GH_PAT（需要 repo + read:user 权限）
export $(cat .env | xargs)
python scripts/fetch_mcp.py  # 40 个包约 6-9 分钟（受 10 次/分钟限制）
python scripts/fetch_skills.py
python scripts/compose.py    # 合并 → data/rankings/latest.json
```

除 Python 标准库外零依赖、零 API 费用，结果以版本化 JSON 提交入库。

## 为什么开源

1. **数据应当可 fork**——每个快照都是 `data/` 下的版本化 JSON，`git log -- data/mcp-servers/` 即得时间序列，无需注册、不限流。
2. **方法论应当可审计**——权重有偏、查询有漏、漏了热门 MCP？直接 PR。整条流水线就是纯 Python + 标准库。

## 贡献

- **新增 MCP 服务器**：编辑 `scripts/lib/mcp_packages.py` 的 `MCP_PACKAGES`，重跑 `compose.py`。
- **改进打分**：提 Issue 说明思路，权重在 `scripts/compose.py` 调整。
- **Bug**：附上报错栈和 PAT 权限范围（**别贴 token 本身**）。

## FAQ

**Q：代码搜索不是限 9 次/分钟吗？** 对，所以 `fetch_mcp.py` 每次请求间隔 7.5 秒，30 个包约 4 分钟。

**Q：为什么不爬 `/network/dependents` 拿完整 used-by 列表？** GitHub ToS 对爬 HTML 属灰色地带，且 GraphQL 的 `repositoriesDependentsCount` 字段实际不存在（已实测 `undefinedField`）。我们改用 code search 统计清单文件引用数——同样是行为证据，走的是官方 API。

**Q：和 AgentScout / Billboard 有什么不同？** 它们按 star 排，我们按**行为证据**排——配置文件出现频次和依赖边。Star 衡量热度，配置出现衡量真实采用。

## 🤖 Development & AI Disclosure

本项目为 **AI 重度辅助开发**：AI 助手参与了代码生成、测试编写、文档、重构与调试等环节。

- **核心算法经人工复核**：关键逻辑与参数取值均有源码级人工审查，非模型自动断言。
- **测试由 CI 独立执行**：所有测试在 GitHub Actions 上运行，可自行复现。
- **如有夸大请指正**：若发现任何不实的表述，请开 issue 指正——准确性优先于宣传。

## 许可证

MIT — 见 [LICENSE](LICENSE)。
