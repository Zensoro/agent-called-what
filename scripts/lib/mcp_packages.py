"""
MCP server seed list — pre-filled popular packages.
Agent reads this on first run; community can PR new entries.
Last curated: 2026-08-06
"""

from __future__ import annotations

# Curated list of well-known MCP servers (npm/pypi).
# Format: (package_name, registry, category)
# registry: "npm" | "pypi" | "git"
# category: used for tagging in the final report

MCP_PACKAGES = [
    # ── Filesystem & OS ──────────────────────────────────────────────
    ("@modelcontextprotocol/server-filesystem", "npm", "filesystem"),
    ("@modelcontextprotocol/server-github",     "npm", "devops"),
    ("@modelcontextprotocol/server-git",        "npm", "devops"),
    ("@modelcontextprotocol/server-slack",      "npm", "communication"),
    ("@modelcontextprotocol/server-postgres",   "npm", "database"),
    ("@modelcontextprotocol/server-sqlite",     "npm", "database"),
    ("@modelcontextprotocol/server-memory",     "npm", "memory"),
    ("@modelcontextprotocol/server-brave-search","npm","search"),
    ("@modelcontextprotocol/server-fetch",      "npm", "web"),
    ("@modelcontextprotocol/server-puppeteer", "npm", "web"),

    # ── Anthropic official ───────────────────────────────────────────
    ("@anthropic-ai/mcp-server-filesystem",    "npm", "filesystem"),
    ("@anthropic-ai/mcp-server-github",        "npm", "devops"),

    # ── Community popular ────────────────────────────────────────────
    ("mcp-server-sqlite",                       "pypi","database"),
    ("mcp-server-postgres",                    "pypi","database"),
    ("mcp-server-redis",                       "pypi","database"),
    ("mcp-server-mongodb",                     "pypi","database"),
    ("mcp-server-docker",                      "pypi","devops"),
    ("mcp-server-kubernetes",                  "pypi","devops"),
    ("mcp-server-aws",                         "pypi","cloud"),
    ("mcp-server-gcp",                         "pypi","cloud"),
    ("mcp-server-azure",                       "pypi","cloud"),

    # ── Web & scraping ───────────────────────────────────────────────
    ("@modelcontextprotocol/server-google-maps","npm","web"),
    ("mcp-server-youtube",                     "pypi","web"),
    ("mcp-server-twitter",                     "pypi","social"),
    ("mcp-server-discord",                     "pypi","communication"),
    ("mcp-server-notion",                      "pypi","productivity"),

    # ── AI / ML ──────────────────────────────────────────────────────
    ("mcp-server-openai",                      "pypi","ai"),
    ("mcp-server-huggingface",                 "pypi","ai"),
    ("mcp-server-replicate",                   "pypi","ai"),

    # ── Productivity ─────────────────────────────────────────────────
    ("mcp-server-google-drive",               "pypi","productivity"),
    ("mcp-server-gmail",                       "pypi","communication"),
    ("mcp-server-calendar",                    "pypi","productivity"),
    ("mcp-server-todoist",                     "pypi","productivity"),

    # ── Code & docs ──────────────────────────────────────────────────
    ("mcp-server-stripe",                      "pypi","fintech"),
    ("mcp-server-sentry",                      "pypi","observability"),
    ("mcp-server-linear",                      "pypi","productivity"),
    ("mcp-server-jira",                        "pypi","productivity"),
    ("mcp-server-confluence",                  "pypi","productivity"),

    # ── Long-context memory ──────────────────────────────────────────
    ("mem0-mcp",                               "pypi","memory"),
    ("graphiti-mcp",                           "pypi","memory"),
]

# Repos under anthropics/skills that we track as "Agent Skills"
SKILL_REPOS = [
    "anthropics/skills",
    # Add individual skill sub-repos as the ecosystem grows
]

# "Agent-friendly" libs — popular libs likely to be called by agents
# (curated by hand; agent may extend via code-search signal)
AGENT_FRIENDLY_LIBS = [
    "langchain-ai/langchain",
    "langchain-ai/langgraph",
    "microsoft/autogen",
    "crewAIInc/crewAI",
    "run-llama/llama_index",
    "langgenius/dify",
    "cohere-ai/cohere-toolkit",
    "modelcontextprotocol/python-sdk",
    "modelcontextprotocol/typescript-sdk",
    "openai/openai-agents-python",
    "vercel/ai",
    "mastra-ai/mastra",
    "agno-agi/agno",
    "pydantic/pydantic-ai",
    "jina-ai/serve",
]


def get_by_category(category: str | None = None) -> list[tuple[str, str, str]]:
    """Return packages, optionally filtered by category."""
    if category is None:
        return list(MCP_PACKAGES)
    return [p for p in MCP_PACKAGES if p[2] == category]


if __name__ == "__main__":
    print(f"Total MCP packages tracked: {len(MCP_PACKAGES)}")
    cats = sorted({p[2] for p in MCP_PACKAGES})
    for c in cats:
        print(f"  {c}: {len(get_by_category(c))}")
