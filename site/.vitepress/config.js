import { defineConfig } from 'vitepress'

// Read rankings JSON at build time
import fs from 'node:fs'
import path from 'node:path'

const dataPath = path.resolve('..', 'data', 'rankings', 'latest.json')
let rankings = { methodology: {}, tables: { mcp_servers: [], agent_skills: [] } }
try {
  rankings = JSON.parse(fs.readFileSync(dataPath, 'utf-8'))
} catch (e) {
  console.warn('⚠️  No data/rankings/latest.json found — site will show empty tables. Run scripts first.')
}

function tableRows(rows, cols) {
  return rows.slice(0, 30).map((r, i) => {
    const cells = cols.map(c => String(r[c] ?? ''))
    return `| ${i + 1} | ${cells.join(' | ')} |`
  }).join('\n')
}

const mcpCols   = ['package', 'call_count', 'npm_monthly_dl', 'weekly_delta', 'score']
const skillCols = ['repo', 'dependents', 'stars', 'delta_stars', 'score']

const mcpTable = `
## 🔌 MCP Servers Top 30

*Updated: ${rankings.generated_at || 'pending'}*

| # | Package | Call Count | npm DL/mo | Δ (week) | Score |
|---|---|---|---|---|---|
${tableRows(rankings.tables?.mcp_servers || [], mcpCols)}
`

const skillTable = `
## 🧩 Agent Skills & Libraries Top 30

*Updated: ${rankings.generated_at || 'pending'}*

| # | Repo | Used-By | Stars | Δ Stars | Score |
|---|---|---|---|---|---|
${tableRows(rankings.tables?.agent_skills || [], skillCols)}
`

export default defineConfig({
  title: 'agent-called-what',
  description: 'Behavior-based rankings of what AI agents actually call on GitHub',
  lang: 'en-US',
  // GitHub Pages project site → repo-name base path
  base: '/agent-called-what/',
  themeConfig: {
    nav: [
      { text: 'MCP Servers', link: '/mcp' },
      { text: 'Agent Skills', link: '/skills' },
      { text: 'Methodology', link: '/methodology' },
      { text: 'GitHub', link: 'https://github.com/Zensoro/agent-called-what' }
    ],
    sidebar: {
      '/': [
        { text: 'Rankings', items: [
          { text: 'MCP Servers', link: '/mcp' },
          { text: 'Agent Skills', link: '/skills' }
        ]},
        { text: 'About', items: [
          { text: 'Methodology', link: '/methodology' },
          { text: 'Contributing', link: '/contributing' }
        ]}
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Zensoro/agent-called-what' }
    ],
    footer: {
      message: 'MIT License — data is free to reuse',
      copyright: 'agent-called-what contributors'
    }
  },
  // Inject generated tables into pages
  transformPageData(pageData) {
    if (pageData.relativePath === 'mcp.md') {
      pageData.frontmatter = pageData.frontmatter || {}
    }
  },
  markdown: {
    config: (md) => {
      // custom block for auto-generated tables
    }
  },
  // We'll write the tables as static MD files instead — see /mcp.md and /skills.md
})
