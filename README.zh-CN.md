# agent-called-what

> AI 在 GitHub 上到底调了什么？不是 star 榜，**是行为榜**。

市面上所有"AI Agent 排行榜"本质都是 star 计数器套壳。本仓库衡量的是真正重要的事：**真实的 AI Agent 在野外实际接入、调用了哪些 MCP Server、Skill 和库**——证据来自公开的 `mcp.json` 配置文件和仓库依赖图。

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

## 许可证

MIT — 见 [LICENSE](LICENSE)。
