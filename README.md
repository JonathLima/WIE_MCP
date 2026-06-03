# WIE — Web Investigator Engine

> MCP server for web search and content extraction — free, self-hosted, zero-tracking.

[![AGPLv3 License](https://img.shields.io/badge/License-AGPLv3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)

**WIE** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI agents (Claude, Gemini, GPT-4, etc.) the ability to search the web and extract page content. It sits between your AI client and the internet, using a local [SearXNG](https://searxng.github.io/searxng/) instance as its search engine — no external API keys required.

🇧🇷 [Versão em Português](./README.pt-br.md)

---

## How it works

```
AI Agent (Claude, Cursor, Zed...)
        │
        ▼
   MCP Server (WIE)             ← port 8000
   ├── web_search()
   ├── web_search_advanced()
   ├── site_search()
   ├── fetch_page()
   ├── get_contents()
   └── answer()
        │
        ▼
   SearXNG (local)              ← port 8080
   ├── google
   ├── duckduckgo
   ├── bing
   ├── wikipedia
   └── startpage
        │
        ▼
      Internet
```

SearXNG runs locally in Docker. All queries are private — no third-party tracking, no API keys needed.

---

## Requirements

- **Docker** and **Docker Compose**
- **Python 3.11+** (only for STDIO local mode)
- An AI client that supports the MCP protocol

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/your-user/WIE_MCP.git
cd WIE_MCP
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and change at least `SEARXNG_SECRET`:

```env
SEARXNG_SECRET=replace-with-a-random-secure-string
```

### 3. Start the services

```bash
docker compose up -d
```

This starts two containers:
- **wie-mcp-server** — the MCP server, on port `8000`
- **wie-searxng** — SearXNG, on port `8080`

Wait ~30 seconds for SearXNG to fully initialize.

### 4. Verify

```bash
# Check containers are running
docker ps

# View MCP server logs
docker logs wie-mcp-server

# View SearXNG logs
docker logs wie-searxng
```

---

## MCP client configuration

### HTTP mode (recommended with Docker)

Use when the server is running via `docker compose up`. The server is available at `http://localhost:8000/mcp`.

**For Claude Desktop, Cursor, Windsurf, VS Code Cline, LM Studio:**

```json
{
  "mcpServers": {
    "wie": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

> **Reference files:** `configs/http-remote.json`, `configs/lm-studio.json`

### STDIO mode (local, no Docker for MCP)

Use when you want to run the MCP server directly in your terminal (SearXNG still needs to be running).

**Prerequisites:** install Python dependencies:

```bash
python -m venv venv
.\venv\Scripts\activate      # Windows
# or: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

**Configuration:**

```json
{
  "mcpServers": {
    "wie": {
      "command": "python",
      "args": ["-m", "src.server", "stdio"]
    }
  }
}
```

> **Reference files:** `configs/claude-desktop.json`, `configs/cursor.json`, `configs/zed.json`, `configs/windsurf.json`, `configs/vscode-cline.json`

### Where to place the config

| Client | Configuration file path |
|--------|------------------------|
| Claude Desktop (Mac) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | Settings → MCP → Add new server |
| Zed | `.zed/settings.json` |
| Windsurf | Settings → MCP → Add new server |
| VS Code + Cline | `.vscode/mcp.json` |
| LM Studio | Settings → MCP Servers |

---

## Available tools

WIE exposes **6 MCP tools**:

### `web_search` — general web search

Multi-engine search with source authority tier scoring (tiers 1–4) and optional FlashRank reranking.

```python
web_search(
    query="Python 3.13 release notes",
    time_range="month",   # hour | day | week | month | year (optional)
    categories="news",    # general | news | images | videos | it | science (optional)
    safesearch="0",       # "0"=off | "1"=moderate | "2"=strict (optional)
    limit=10,             # 1–20, default: 10
)
```

---

### `web_search_advanced` — advanced search with filters

Search with query expansion, domain filters, date filters, category targeting, and variable depth modes.

```python
web_search_advanced(
    query="impact of LLMs on software development",
    search_type="deep",               # see table below
    num_results=15,                   # default: 10
    category="research_paper",        # see categories below
    include_domains=["arxiv.org"],    # only these domains
    exclude_domains=["reddit.com"],   # ignore these domains
    start_published_date="2024-01-01",  # YYYY-MM-DD
    end_published_date="2025-01-01",
    include_text=["transformer"],     # page must contain these words
    exclude_text=["tutorial"],        # page must not contain these words
    safesearch=0,                     # 0 | 1 | 2
    enable_highlights=True,           # extract relevant passages
    highlight_sentences=3,            # sentences per passage (default: 3)
    enable_summary=False,             # extractive summary per result
    additional_queries=True,          # use query expansion for deep modes
)
```

**Search types (`search_type`):**

| Type | Query variations | Reranking | Highlights | Use case |
|------|-----------------|-----------|------------|----------|
| `instant` | 1 | ❌ | ❌ | Ultra-fast, top 3 results |
| `fast` | 1 | ❌ | ❌ | Quick, single-pass search |
| `auto` | 1 | ✅ | ✅ | **Default** — best balance |
| `deep_lite` | 3 | ✅ | ✅ | Moderate research |
| `deep` | 5 | ✅ | ✅ | Thorough research |
| `deep_reasoning` | 7 | ✅ | ✅ | Complex investigation |

**Categories (`category`):**

| Category | Prioritized domains |
|----------|---------------------|
| `general` | All engines |
| `news` | BBC, Reuters, AP News, NYT, The Guardian |
| `research_paper` | arXiv, Nature, IEEE, ACM, NeurIPS |
| `company` | LinkedIn, Bloomberg, Crunchbase |
| `people` | LinkedIn, GitHub, Google Scholar |
| `financial_report` | SEC EDGAR |
| `product` | Product Hunt, G2, Capterra |
| `personal_site` | Medium, Dev.to, Substack |
| `code` | GitHub, GitLab, Stack Overflow |
| `video` | YouTube, Vimeo, TED |
| `image` | Unsplash, Flickr, Pexels |

---

### `site_search` — search within a specific domain

Issues a `site:domain query` search — useful for finding official documentation or domain-specific content.

```python
site_search(
    query="async io concurrency",
    site="docs.python.org",
    time_range="year",   # optional
    limit=5,             # default: 5
)
```

---

### `fetch_page` — extract content from a URL

Extracts clean text content from a web page. Tries `curl-cffi` (anti-bot stealth) first, falls back to `nodriver` (headless browser), then `httpx`.

```python
fetch_page(
    url="https://docs.python.org/3/whatsnew/3.13.html",
    max_tokens=8000,   # optional, default: 8000
)
```

Returns: title, description, headings, main content, tables, JSON-LD structured data, and a link summary.

---

### `get_contents` — fetch content from multiple URLs

Parallel fetch of up to 20 URLs (max 3 concurrent). Can extract highlights and summaries per page.

```python
get_contents(
    urls=[
        "https://arxiv.org/abs/2401.04012",
        "https://github.com/openai/gpt-2",
    ],
    highlight_query="large language model training",   # optional
    highlight_sentences=3,                              # default: 3
    enable_summary=False,                               # default: False
    max_tokens=8000,                                    # per URL, default: 8000
)
```

---

### `answer` — direct answer from URLs

Fetches the provided URLs, extracts the most relevant passages for the question, and returns an extractive answer.

```python
answer(
    query="What is the maximum context window for Claude 3.5?",
    urls=["https://docs.anthropic.com/en/docs/about-claude/all-releases"],
)
```

---

## Source authority tiers

All search results are classified into 4 reliability tiers:

| Tier | Emoji | Description | Examples |
|------|-------|-------------|----------|
| Tier 1 | 🟢 | Official / Definitive | `github.com`, `docs.python.org`, `.gov`, `.edu` |
| Tier 2 | 🔵 | Authoritative | `wikipedia.org`, `stackoverflow.com`, `arxiv.org` |
| Tier 3 | 🟡 | Reference | `medium.com`, `reuters.com`, `dev.to` |
| Tier 4 | ⚪ | General | Generic blogs, Reddit, SEO content |

---

## Environment variables

All variables are configured in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARXNG_HOST` | `http://searxng:8080` | Internal SearXNG URL |
| `SEARXNG_ENGINES` | `google,duckduckgo,bing,wikipedia,startpage` | Active engines (comma-separated) |
| `SEARXNG_DEFAULT_CATEGORY` | `general` | Default category when not specified |
| `SEARXNG_SAFESEARCH` | `0` | Safe search level: `0`, `1`, or `2` |
| `SEARXNG_SECRET` | *(required)* | SearXNG secret key — **change before use** |
| `SEARCH_DEFAULT_TYPE` | `auto` | Default search type: `instant`, `fast`, `auto`, `deep_lite`, `deep`, `deep_reasoning` |
| `SEARCH_DEFAULT_LIMIT` | `10` | Default result limit (1–20) |
| `SEARCH_TIMEOUT_SECONDS` | `10` | Search timeout in seconds |
| `FETCH_TIMEOUT_SECONDS` | `15` | Page fetch timeout in seconds |
| `FETCH_MAX_CONTENT_LENGTH` | `10000` | Max characters extracted per page |
| `FETCH_TOKEN_BUDGET` | `8000` | Token budget per page |
| `MCP_SERVER_HOST` | `0.0.0.0` | Host address for the MCP server |
| `MCP_SERVER_PORT` | `8000` | MCP server port |
| `API_KEY` | *(empty)* | Optional API key to restrict server access |

---

## Project structure

```
WIE_MCP/
├── src/
│   ├── server.py              # MCP server — registers all 6 tools
│   ├── config.py              # Configuration via Pydantic Settings + .env
│   ├── constants.py           # Domain tiers, search types, categories
│   ├── models.py              # Pydantic schemas (request/response)
│   ├── errors.py              # Typed error classes
│   ├── searxng_client.py      # HTTP client for SearXNG
│   ├── tools/
│   │   ├── web_search.py          # web_search tool
│   │   ├── web_search_advanced.py # web_search_advanced tool
│   │   ├── fetch_page.py          # fetch_page tool
│   │   ├── get_contents.py        # get_contents tool
│   │   ├── site_search.py         # site_search tool
│   │   └── answer.py              # answer tool
│   └── utils/
│       ├── dedup.py               # Result deduplication and scoring
│       ├── highlights.py          # Relevant passage extraction
│       ├── summarizer.py          # Extractive summarization
│       ├── text.py                # Sentence splitter
│       ├── query_expander.py      # Query expansion for deep modes
│       ├── readability.py         # Readable content extraction
│       └── truncation.py          # Token-based truncation
├── configs/
│   ├── claude-desktop.json    # Claude Desktop config (STDIO)
│   ├── cursor.json            # Cursor config (STDIO)
│   ├── zed.json               # Zed config (STDIO)
│   ├── windsurf.json          # Windsurf config (STDIO)
│   ├── vscode-cline.json      # VS Code + Cline config (STDIO)
│   ├── http-remote.json       # HTTP config (Docker)
│   └── lm-studio.json         # LM Studio config (HTTP)
├── searxng/
│   └── settings.yml           # SearXNG configuration
├── docker-compose.yml         # Starts wie-mcp-server + wie-searxng
├── Dockerfile                 # MCP server container image
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── pytest.ini                 # Test configuration
```

---

## Key dependencies

| Package | Purpose |
|---------|---------|
| `mcp` | MCP protocol (FastMCP) |
| `httpx` | Async HTTP requests |
| `pydantic` + `pydantic-settings` | Validation and configuration |
| `beautifulsoup4` + `readability-lxml` | HTML parsing and content extraction |
| `curl-cffi` | HTTP client with bot-detection bypass |
| `nodriver` | Headless browser fallback |
| `flashrank` | Local relevance reranking (optional) |
| `uvicorn` + `starlette` | HTTP server for Streamable HTTP mode |

---

## Useful commands

```bash
# Start everything
docker compose up -d

# Stream logs
docker compose logs -f

# Stop everything
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Run tests
python -m pytest tests/ -v

# Run server locally (STDIO mode)
python -m src.server stdio

# Run server locally (HTTP mode)
python -m src.server http
```

---

## Troubleshooting

### "Connection refused" or "Cannot reach SearXNG"
- Check containers are running: `docker ps`
- Wait ~30s after `docker compose up -d` for SearXNG to fully initialize
- Check logs: `docker logs wie-searxng`

### No search results
- SearXNG may have misconfigured engines
- Check `searxng/settings.yml` and ensure the engines are enabled

### Port already in use
- Change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"   # uses port 8001 on the host
  ```
- Update the client config URL to `http://localhost:8001/mcp`

### Accessing from another machine
- Replace `localhost` with the IP of the machine running Docker:
  ```json
  { "url": "http://192.168.1.100:8000/mcp" }
  ```

---

## License

**GNU Affero General Public License v3 (AGPLv3)** — [LICENSE](LICENSE)

Copyright © 2025–2026 Jonathan Lima
