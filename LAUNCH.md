# LAUNCH.md — Pre-written launch posts

Use these when v0.1 is ready. Adapt tone to each platform. Replace repo URL if you fork under a different name.

---

## Hacker News

**Title:** Show HN: What AI agents actually call on GitHub (behavior-based, not star-based)

**Body:**

Every "AI agent top N" list is just a star counter. I wanted to know what agents are *actually wired up to*, so I built a small open-source pipeline that measures behavioral evidence instead:

- Scans public `mcp.json` files on GitHub via code search → counts how often each MCP server appears
- Counts manifest-file references (package.json / requirements.txt / pyproject.toml) for skill/lib repos
- Blends in npm download velocity
- Composite score: 40% call-count, 25% dependents, 20% downloads, 15% stars

All data is versioned JSON in `data/` — clone the repo, run three Python scripts, reproduce the rankings bit-for-bit. No API keys to buy, no "pro tier."

Would love feedback on the methodology (especially the weighting) and obviously PRs for new MCP servers.

Repo: https://github.com/Zensoro/agent-called-what

---

## r/LocalLlama (Reddit)

**Title:** I built a behavior-based ranking of what AI agents actually use (not star-based) — open source, reproducible

**Body:**

Most agent rankings = star counters. I tried to measure something closer to *actual adoption*:

1. GitHub code search for `"<mcp-pkg>" filename:mcp.json` → how many real agent configs reference it
2. Code-search manifest references for skill/lib repos
3. npm last-month downloads as a sanity check

Formula + raw data + scripts all in the repo. It's ~150 lines of Python, no dependencies beyond stdlib.

Looking for: (a) MCP servers I missed in the seed list, (b) pushback on the weights, (c) ideas for the v0.2 PyPI signal.

Repo: https://github.com/Zensoro/agent-called-what

---

## 即刻 / 掘金 / V2EX (中文)

**标题：** 我做了一份「AI 实际调用榜」，不数 star，数 mcp.json

**正文：**

市面上所有 AI Agent 排行榜本质都是 star 计数器。我想知道 AI 真正在调什么，于是做了个开源小工具：

- 用 GitHub 代码搜索扫所有公开 `mcp.json`，统计每个 MCP 服务器被引用次数
- 用 code search 数清单文件引用（package.json / requirements.txt / pyproject.toml）衡量 skill/库的被引用度
- 叠 npm 月下载量做 sanity check
- 复合打分，权重和方法论全写在仓库里

整套代码 ~150 行 Python，标准库就够，数据全部版本化 JSON 存 `data/`，可复现、可 fork。

求三样东西：(1) 我漏掉的热门 MCP 服务器；(2) 对权重的吐槽；(3) v0.2 想加 PyPI 信号的实现建议。

仓库：https://github.com/Zensoro/agent-called-what

---

## X / Twitter

📊 What do AI agents ACTUALLY call on GitHub?

Not stars. Not hype. Real `mcp.json` configs + dependency graphs.

I built `agent-called-what` — open-source, ~150 LOC Python, fully reproducible.

Scans public MCP configs → ranks by behavioral evidence.

Repo: https://github.com/Zensoro/agent-called-what

#AIAgents #MCP #OpenSource

---

## DevTools / AI Newsletters (pitch)

Subject: New open dataset: behavioral rankings for AI agent tools

Body: Hi [name], I maintain agent-called-what, an open-source project that publishes weekly rankings of MCP servers, agent skills, and libraries based on *behavioral evidence* (public agent config files + dependency graphs) rather than GitHub stars. All data is versioned JSON, free to reuse. Thought it might be useful for your readers — happy to write a short guest post explaining the methodology. Repo: https://github.com/Zensoro/agent-called-what
