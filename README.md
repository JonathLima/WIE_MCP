# WIE - Web Investigator Engine

> **Privacy-first, unlimited, zero-cost neural search for AI agents**

[![AGPLv3 License](https://img.shields.io/badge/License-AGPLv3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)

A high-precision Model Context Protocol (MCP) server that provides deep investigation tools for LLMs. Built on the **Investigator Pattern**: rich metadata and deep content extraction enable models (Claude, Gemini, GPT-4) to perform factually perfect research — without complex prompts.

🇧🇷 [Versão em Português](./README.pt-br.md)

---

## ✨ Why WIE - Web Investigator Engine?

| Feature | Exa Search | WIE - Web Investigator Engine |
|---------|-----------|----------------------|
| **Cost** | Paid tier | Free & open-source |
| **Privacy** | Data may be logged | Zero-logging, self-hosted |
| **Customization** | Limited | Full source access |
| **Infrastructure** | External API dependency | Run on your own hardware |
| **Transparency** | Proprietary black box | Fully transparent |
| **Speed** | Fast | Tuned for LLM efficiency |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP SERVER                                        │
│                     (Investigator Pattern)                                 │
│                                                                             │
│   ┌──────────────────┐  ┌───────────────────────┐  ┌──────────────────┐   │
│   │  web_search()    │  │ web_search_advanced()  │  │  site_search()   │   │
│   │  (Discovery)      │  │ (Full Exa parity)    │  │  (Definitive)    │   │
│   └──────────────────┘  └───────────────────────┘  └──────────────────┘   │
│                                                                             │
│   ┌──────────────────┐  ┌───────────────────────┐                          │
│   │  fetch_page()    │  │   get_contents()      │                          │
│   │  (Single URL)     │  │   (Batch + Highlights)│                          │
│   └──────────────────┘  └───────────────────────┘                          │
│                                                                             │
│   ┌───────────────────────┐                                                 │
│   │      answer()          │  (Extractive QA)                               │
│   └───────────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND LAYER                                        │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │    SearxNG     │  │   FlashRank     │  │    Content Extraction       │  │
│  │  Multi-Engine   │  │   Reranking     │  │  curl_cffi → nodriver → httpx│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔎 Search Types

| Type | Description | Use Case |
|------|-------------|----------|
| **`auto`** | Best overall — balanced speed/quality | General research, first-pass discovery |
| **`fast`** | Instant results, minimal processing | Quick facts, single-engine, no rerank |
| **`instant`** | Sub-second, ultra-lean results | "I'm feeling lucky" — top 3 results only |
| **`deep-lite`** | Light deep research — 3 query variations | Background research, initial investigation |
| **`deep`** | Full deep research — 5 query variations | Comprehensive reports, detailed analysis |
| **`deep-reasoning`** | Multi-step chain-of-thought — 7+ variations | Complex investigations, multi-perspective synthesis |

---

## ⚡ Speed vs Quality

Choose the right search type based on your speed/quality needs:

| Type | Speed | Queries | Rerank | Best For |
|------|-------|---------|--------|-------------|
| `instant` | ⚡⚡⚡ Very fast | 1 | Quick facts, "I'm feeling lucky" |
| `fast` | ⚡⚡ Fast | 1 | General quick search |
| `auto` | ⚡ Balanced | 1 | **Default** — recommended |
| `deep_lite` | 🐢 Slow | 3 | Background research |
| `deep` | 🐢🐢 Slower | 5 | Comprehensive reports |
| `deep_reasoning` | 🐢🐢🐢 Slowest | 7+ | Complex investigations |

### Speed Configuration via .env

For maximum speed, edit your `.env` file:

```bash
# Maximum speed (1 engine, 5s timeout, fast mode)
SEARXNG_ENGINES=google
SEARCH_TIMEOUT_SECONDS=5
SEARCH_DEFAULT_TYPE=fast
```

For maximum quality, use deep modes in your calls:

```python
web_search_advanced({
    "query": "your topic",
    "type": "deep",  # or "deep_reasoning"
    "numResults": 20
})
```

---

## 📂 Categories

Filter results by content type for more targeted research:

| Category | Description | Best For |
|----------|-------------|----------|
| **`general`** | General web content | Broad topics |
| **`news`** | News articles and outlets | Current events, breaking news |
| **`research_paper`** | Scholarly articles, arxiv | Academic research, citations |
| **`company`** | Business sites, org pages | Company profiles, business info |
| **`people`** | Biography, profiles, social | Person lookup, biographical info |
| **`financial_report`** | SEC filings, earnings, PDFs | Investment research, financial analysis |
| **`product`** | Product pages, e-commerce | Product specifications, reviews |
| **`personal_site`** | Blogs, portfolios, indie sites | Expert opinions, personal insights |
| **`code`** | GitHub, StackOverflow, docs | Code examples, documentation |
| **`video`** | Video content | Tutorials, visual demonstrations |
| **`image`** | Images and visual content | Visual references, diagrams |

---

## 🛠️ Tool Reference

### `web_search` — Discovery Search

Basic multi-engine search with authority tier scoring.

```python
{
  "query": "latest Python release 2025",
  "time_range": "day",        # hour, day, week, month, year
  "categories": "news",       # general, news, images, videos, it, science
  "safesearch": "0",          # 0=off, 1=moderate, 2=strict
  "limit": 10                 # 1-20 results
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `string` | **Required** | Search query string |
| `time_range` | `string` | `null` | Filter: `hour`, `day`, `week`, `month`, `year` |
| `categories` | `string` | `null` | Category filter |
| `safesearch` | `string` | `null` | Safe search: `0`, `1`, `2` |
| `limit` | `int` | `10` | Results 1-20 |

---

### `web_search_advanced` — Advanced Exa-Style Search

Full-featured search with all filter options, highlights, and summaries.

```python
{
  "query": "OpenAI GPT-5 release date",
  "type": "deep",
  "numResults": 20,
  "category": "news",
  "includeDomains": ["reuters.com", "bloomberg.com"],
  "startPublishedDate": "2025-01-01",
  "enableHighlights": True,
  "enableSummary": True
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `string` | **Required** | Search query |
| `type` | `SearchType` | `"auto"` | Search type: `auto`, `fast`, `instant`, `deep_lite`, `deep`, `deep_reasoning` |
| `numResults` | `int` | `10` | Results count (1-100) |
| `category` | `Category` | `null` | Category filter |
| `includeDomains` | `list[string]` | `null` | Required domains |
| `excludeDomains` | `list[string]` | `null` | Blocked domains |
| `startPublishedDate` | `string` | `null` | ISO date — published after |
| `endPublishedDate` | `string` | `null` | ISO date — published before |
| `startCrawlDate` | `string` | `null` | ISO date — crawled after |
| `endCrawlDate` | `string` | `null` | ISO date — crawled before |
| `includeText` | `list[string]` | `null` | Required phrases in page |
| `excludeText` | `list[string]` | `null` | Excluded phrases |
| `userLocation` | `object` | `null` | `{"country": "US", "city": "NYC"}` |
| `safesearch` | `int` | `0` | 0=off, 1=moderate, 2=strict |
| `enableHighlights` | `bool` | `true` | Include query-matched highlights |
| `highlight_sentences` | `int` | `3` | Sentences per highlight (1-10) |
| `enableSummary` | `bool` | `false` | Include extractive summary |
| `additionalQueries` | `bool` | `true` | Enable query expansion for deep modes |

---

### `get_contents` — Batch Content Retrieval

Fetch multiple URLs simultaneously with highlights and summaries.

```python
{
  "urls": [
    "https://arxiv.org/abs/2401.04012",
    "https://github.com/openai/gpt-5"
  ],
  "highlight_query": "GPT-5 architecture capabilities",
  "highlight_sentences": 5,
  "enableSummary": True,
  "max_tokens": 8000
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `urls` | `list[string]` | **Required** | URLs to fetch (1-20) |
| `highlight_query` | `string` | `null` | Query for highlight extraction |
| `highlight_sentences` | `int` | `3` | Sentences per highlight |
| `enableSummary` | `bool` | `false` | Include extractive summary |
| `max_tokens` | `int` | `8000` | Per-URL token budget (500-128000) |

---

### `answer` — Extractive Question Answering

Extract answers directly from source documents.

```python
{
  "query": "What is the main contribution of this paper?",
  "urls": ["https://arxiv.org/abs/2401.04012"]
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `string` | **Required** | Question to answer |
| `urls` | `list[string]` | **Required** | Source URLs (1-20) |

---

### `site_search` — Definitive Truth Search

Search within a specific domain for authoritative results.

```python
{
  "query": "async io release notes",
  "site": "docs.python.org"
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `string` | **Required** | Search query |
| `site` | `string` | **Required** | Target domain (e.g., `github.com`, `docs.rs`) |

---

### `fetch_page` — Single Page Extraction

Extract clean markdown content from a single URL.

```python
{
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "max_tokens": 16000
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `string` | **Required** | Full page URL |
| `max_tokens` | `int` | `null` | Token budget override (500-128000) |

---

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/your-user/SearchEngineLLM.git
cd SearchEngineLLM
cp .env.example .env
# Edit .env: change SEARXNG_SECRET to a secure random string
```

### 2. Start with Docker

```bash
docker compose up -d
```

### 3. Configure Your MCP Client

This server supports both **STDIO** (local) and **HTTP** (remote) transport.

#### STDIO Mode

```bash
python -m src.server
```

```json
{
  "mcpServers": {
    "investigator": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

#### HTTP Mode (Remote)

```bash
python -m src.server http
# Server runs at http://localhost:8000/mcp
```

```json
{
  "mcpServers": {
    "investigator": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## 💻 Client Configurations

### Claude Desktop

**File:** `configs/claude_desktop.json`

```json
{
  "mcpServers": {
    "investigator": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {}
    }
  }
}
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`

---

### Cursor

**File:** `configs/cursor.json`

```json
{
  "mcpServers": {
    "investigator": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

Settings → MCP → Add new server

---

### Zed

**File:** `configs/zed.json`

```json
{
  "mcpServers": {
    "investigator": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

`.zed/config.json`

---

### Windsurf

**File:** `configs/windsurf.json`

```json
{
  "mcpServers": {
    "investigator": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

Settings → MCP → Add new server

---

### VS Code / Cline

**File:** `configs/vscode.json`

```json
{
  "mcpServers": {
    "investigator": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

`.vscode/mcp.json`

---

### LM Studio (HTTP)

```bash
python -m src.server http
```

**File:** `configs/lm-studio.json`

```json
{
  "mcpServers": {
    "investigator": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## 📖 Usage Examples

### Basic Search

```
web_search({
  "query": "latestSpaceX Starship launch",
  "time_range": "day"
})
```

### Advanced Deep Research

```
web_search_advanced({
  "query": "impact of LLMs on software development",
  "type": "deep",
  "category": "research_paper",
  "numResults": 20,
  "enableHighlights": true,
  "enableSummary": true
})
```

### Batch Content Fetch with Highlights

```
get_contents({
  "urls": [
    "https://arxiv.org/abs/2401.04012",
    "https://github.com/anthropic/claude-code"
  ],
  "highlight_query": "LLM code generation capabilities",
  "enableSummary": true
})
```

### Extractive Q&A

```
answer({
  "query": "What is the context window size for Claude 3.5?",
  "urls": ["https://docs.anthropic.com/en/docs/about-claude/all-releases"]
})
```

### Domain-Specific Search

```
site_search({
  "query": "async io concurrency",
  "site": "docs.python.org"
})
```

### Category-Specific Research

```
web_search_advanced({
  "query": "Tesla stock performance 2024",
  "type": "deep",
  "category": "financial_report",
  "startPublishedDate": "2024-01-01"
})

web_search_advanced({
  "query": "machine learning transformers attention",
  "type": "deep",
  "category": "research_paper",
  "includeDomains": ["arxiv.org", "papers.nips.cc"]
})

web_search_advanced({
  "query": "John Carmack career biography",
  "type": "deep",
  "category": "people"
})
```

---

## 🤖 Agent Skills

Ready-to-use research prompts for autonomous investigation.

### Company Research

```
You are a professional company researcher. Investigate [COMPANY NAME] using the following approach:

1. Use web_search_advanced with category="company" to find official sources
2. Search for recent news, financial reports, and official statements
3. Use get_contents to extract detailed information from their website and press releases
4. Use answer to extract key facts about products, leadership, and recent developments
5. Compile findings into a comprehensive company profile with:
   - Company overview and mission
   - Recent performance and news
   - Leadership and key personnel
   - Products or services offered
   - Financial position (if public)
```

### People Search

```
You are a professional investigator specializing in people search. Find comprehensive information about [PERSON NAME] by:

1. Use web_search_advanced with category="people" for biographical sources
2. Search for professional profiles (LinkedIn, Crunchbase), Wikipedia, and personal websites
3. Use get_contents to extract detailed biographical information
4. Use answer to extract career history, achievements, and notable facts
5. Return a detailed profile including:
   - Professional background and career
   - Notable achievements and contributions
   - Current affiliation
   - Educational background
```

### Research Paper Investigation

```
You are an academic researcher. Conduct a thorough investigation of [TOPIC/ PAPER] by:

1. Use web_search_advanced with category="research_paper", targeting arxiv.org and academic databases
2. Search for the paper title, authors, and key concepts
3. Use get_contents to extract the full paper content
4. Use answer to extract:
   - Main contribution and innovations
   - Methodology used
   - Key results and conclusions
   - Limitations and future work
5. Return a structured academic summary with citations
```

### Financial Report Analysis

```
You are a financial analyst. Analyze [COMPANY/TOPIC] financial reports by:

1. Use web_search_advanced with category="financial_report" to find SEC filings, earnings reports
2. Search for annual reports (10-K), quarterly reports (10-Q), and investor presentations
3. Use get_contents to extract detailed financial data
4. Use answer to extract key financial metrics, ratios, and narrative
5. Return a financial summary with:
   - Revenue and profit trends
   - Key financial ratios
   - Significant events or changes
   - Investment highlights and risks
```

### Code Context for Development

```
You are a senior software engineer. Investigate [LIBRARY/ FRAMEWORK/ API] for code context by:

1. Use web_search_advanced with category="code", targeting GitHub, StackOverflow, and official docs
2. Search for usage examples, tutorials, and API documentation
3. Use get_contents to extract code examples and official documentation
4. Use answer to extract:
   - API signatures and parameters
   - Common usage patterns
   - Best practices and gotchas
   - Version compatibility information
5. Return comprehensive code documentation with examples
```

### Deep Investigation

```
You are a senior investigative researcher. Conduct a deep investigation of [COMPLEX TOPIC] using chain-of-thought reasoning:

1. Use web_search_advanced with type="deep_reasoning" for comprehensive multi-perspective analysis
2. Generate multiple query variations to explore different angles:
   - Historical background and origins
   - Current state and recent developments
   - Key stakeholders and perspectives
   - Controversies and debates
   - Future implications and predictions
3. Use get_contents to extract detailed information from authoritative sources
4. Use answer to synthesize findings across multiple sources
5. Cross-reference claims and identify consensus vs. disputed points
6. Return a comprehensive investigation report with:
   - Executive summary
   - Detailed findings from each perspective
   - Evidence and citations
   - Areas of consensus and dispute
   - Implications and recommendations
```

---

## 📊 Authority Tiers

Results are classified by source reliability:

| Tier | Description | Examples |
|------|-------------|----------|
| **🟢 Tier 1** | Definitive / Official | `docs.python.org`, `github.com`, `.gov`, `.edu` |
| **🔵 Tier 2** | Authoritative | Wikipedia, Stack Overflow, Arxiv |
| **🟡 Tier 3** | Reference | Tech blogs, News outlets, Publications |
| **⚪ Tier 4** | Other | Reddit, Generic blogs, SEO content |

---

## 📁 Project Structure

```
SearchEngineLLM/
├── src/
│   ├── server.py                  # MCP server entry point
│   ├── config.py                  # Pydantic settings & configuration
│   ├── models.py                  # Request/response schemas
│   ├── errors.py                  # Error classes
│   └── tools/
│       ├── web_search.py          # Basic discovery search
│       ├── web_search_advanced.py # Full Exa-parity advanced search
│       ├── web_fetch.py           # Single URL content extraction
│       ├── get_contents.py         # Batch content + highlights
│       ├── site_search.py          # Domain-specific search
│       └── answer.py               # Extractive Q&A
├── configs/                        # MCP client configurations
├── docs/
│   └── superpowers/
│       └── specs/                 # Design specifications
├── docker-compose.yml             # Docker Compose (MCP + SearxNG)
├── Dockerfile                     # Container definition
├── requirements.txt              # Python dependencies
└── .env.example                 # Environment template
```

---

## 🐳 Docker Deployment

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

Services:
- **wie-mcp-server**: WIE MCP server on port 8000
- **wie-searxng**: Meta-search engine on port 8080

---

## 🔒 Security

- **SSRF protection**: DNS validation, private IP blocking
- **URL validation**: Scheme and netloc required
- **API key middleware**: Optional Bearer token auth
- **Zero logging**: No user data stored or logged

---

## 📜 License

**GNU Affero General Public License v3 (AGPLv3)** — [LICENSE](LICENSE)

Copyright (C) 2025-2026 Jonathan Lima

---

## 🔧 Troubleshooting

### "Connection refused"
- Check if container is running: `docker ps`
- Check logs: `docker logs wie-mcp-server`

### "Timeout"
- Use the URL `/mcp` (Streamable HTTP), not `/sse`

### "Invalid params"
- Verify the URL is correct: must end with `/mcp`

### Remote Access

To access from another computer, replace `localhost` with the host IP:

```json
{
  "mcpServers": {
    "investigator": {
      "url": "http://192.168.1.100:8000/mcp"
    }
  }
}
```

### Environment Variables

WIE_MCP supports standard environment variables configured via system environment or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARXNG_HOST` | Host address of the SearxNG meta-search engine | `http://searxng:8080` |
| `SEARXNG_ENGINES` | Comma-separated engines enabled in SearxNG | `google,duckduckgo,bing,wikipedia,startpage` |
| `SEARXNG_DEFAULT_CATEGORY` | Default search category | `general` |
| `SEARXNG_SAFESEARCH` | Safe search level: `0` (off), `1` (moderate), `2` (strict) | `0` |
| `SEARCH_DEFAULT_TYPE` | Default search mode: `instant`, `fast`, `auto`, `deep_lite`, `deep`, `deep_reasoning` | `auto` |
| `SEARCH_DEFAULT_LIMIT` | Default limit of results returned by discovery search | `10` |
| `SEARCH_TIMEOUT_SECONDS` | Search timeout in seconds | `10.0` |
| `FETCH_TIMEOUT_SECONDS` | Timeout in seconds for page fetching | `15.0` |
| `FETCH_MAX_CONTENT_LENGTH` | Max characters to extract from a web page | `10000` |
| `FETCH_TOKEN_BUDGET` | Approximate token budget for extracted page content | `8000` |
| `MCP_SERVER_HOST` | Host address the MCP server binds to | `0.0.0.0` |
| `MCP_SERVER_PORT` | Port for the MCP server endpoint | `8000` |
| `API_KEY` | Optional API key to restrict access to the server | *(none)* |

### Custom Port

To change the port (e.g., 8090):

```yaml
# docker-compose.yml
ports:
  - "8090:8000"

# Client configuration
"url": "http://localhost:8090/mcp"
```
