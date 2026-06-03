# WIE — Web Investigator Engine

> Servidor MCP de busca e extração de conteúdo web — gratuito, self-hosted e sem rastreamento.

[![Licença AGPLv3](https://img.shields.io/badge/Licença-AGPLv3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)

O **WIE** é um servidor [MCP (Model Context Protocol)](https://modelcontextprotocol.io) que fornece ferramentas de busca e extração de conteúdo web para modelos de linguagem (Claude, Gemini, GPT-4, etc.). Ele funciona como uma camada intermediária entre o agente de IA e a internet — usando o [SearXNG](https://searxng.github.io/searxng/) como mecanismo de busca local.

🇺🇸 [English version](./README.md)

---

## Como funciona

```
Agente de IA (Claude, Cursor, Zed...)
        │
        ▼
   Servidor MCP (WIE)          ← porta 8000
   ├── web_search()
   ├── web_search_advanced()
   ├── site_search()
   ├── fetch_page()
   ├── get_contents()
   └── answer()
        │
        ▼
   SearXNG (local)              ← porta 8080
   ├── google
   ├── duckduckgo
   ├── bing
   ├── wikipedia
   └── startpage
        │
        ▼
      Internet
```

O SearXNG roda localmente via Docker — nenhuma requisição sai identificada, nenhuma API key é necessária.

---

## Pré-requisitos

- **Docker** e **Docker Compose**
- **Python 3.11+** (apenas para modo STDIO local)
- O agente de IA precisa suportar o protocolo MCP

---

## Instalação rápida

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/WIE_MCP.git
cd WIE_MCP
```

### 2. Configurar o ambiente

```bash
cp .env.example .env
```

Edite `.env` e altere pelo menos o `SEARXNG_SECRET`:

```env
SEARXNG_SECRET=troque-por-uma-string-aleatoria-segura
```

### 3. Subir os serviços

```bash
docker compose up -d
```

Isso sobe dois containers:
- **wie-mcp-server** — o servidor MCP, na porta `8000`
- **wie-searxng** — o SearXNG, na porta `8080`

Aguarde ~30 segundos para o SearXNG inicializar completamente.

### 4. Verificar

```bash
# Ver se os containers estão rodando
docker ps

# Ver logs do servidor MCP
docker logs wie-mcp-server

# Ver logs do SearXNG
docker logs wie-searxng
```

---

## Configuração do cliente MCP

### Modo HTTP (recomendado para Docker)

Use quando o servidor está rodando via `docker compose up`. O servidor fica acessível em `http://localhost:8000/mcp`.

**Configuração para Claude Desktop, Cursor, Windsurf, VS Code Cline, LM Studio:**

```json
{
  "mcpServers": {
    "wie": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

> **Arquivo de referência:** `configs/http-remote.json` e `configs/lm-studio.json`

### Modo STDIO (local, sem Docker para o MCP)

Use quando você quer rodar o servidor MCP diretamente no seu terminal, sem Docker (o SearXNG ainda precisa estar rodando).

**Pré-requisito:** instalar as dependências Python:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# ou: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

**Configuração:**

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

> **Arquivo de referência:** `configs/claude-desktop.json`, `configs/cursor.json`, `configs/zed.json`, `configs/windsurf.json`, `configs/vscode-cline.json`

### Onde colocar a configuração

| Cliente | Caminho do arquivo de configuração |
|---------|-----------------------------------|
| Claude Desktop (Mac) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | Settings → MCP → Add new server |
| Zed | `.zed/settings.json` |
| Windsurf | Settings → MCP → Add new server |
| VS Code + Cline | `.vscode/mcp.json` |
| LM Studio | Settings → MCP Servers |

---

## Ferramentas disponíveis

O WIE expõe **6 ferramentas MCP**:

### `web_search` — busca geral

Busca multi-motor com pontuação por autoridade da fonte (tiers 1–4) e rerankig por relevância (FlashRank, quando disponível).

```python
web_search(
    query="Python 3.13 release notes",
    time_range="month",   # hour | day | week | month | year (opcional)
    categories="news",    # general | news | images | videos | it | science (opcional)
    safesearch="0",       # "0"=desligado | "1"=moderado | "2"=estrito (opcional)
    limit=10,             # 1–20, padrão: 10
)
```

---

### `web_search_advanced` — busca avançada com filtros

Busca com expansão de queries, filtros por domínio, datas, categorias e modos de profundidade variáveis.

```python
web_search_advanced(
    query="impacto de LLMs no desenvolvimento de software",
    search_type="deep",              # ver tabela abaixo
    num_results=15,                  # padrão: 10
    category="research_paper",       # ver categorias abaixo
    include_domains=["arxiv.org"],   # apenas esses domínios
    exclude_domains=["reddit.com"],  # ignorar esses domínios
    start_published_date="2024-01-01",  # YYYY-MM-DD
    end_published_date="2025-01-01",
    include_text=["transformer"],    # página deve conter essas palavras
    exclude_text=["tutorial"],       # página não deve conter essas palavras
    safesearch=0,                    # 0 | 1 | 2
    enable_highlights=True,          # extrair trechos relevantes
    highlight_sentences=3,           # qtd de frases por trecho (padrão: 3)
    enable_summary=False,            # resumo extrativo por resultado
    additional_queries=True,         # usar expansão de queries para modos deep
)
```

**Tipos de busca (`search_type`):**

| Tipo | Variações de query | Reranking | Highlights | Uso |
|------|-------------------|-----------|------------|-----|
| `instant` | 1 | ❌ | ❌ | Respostas ultra-rápidas, top 3 |
| `fast` | 1 | ❌ | ❌ | Busca simples e rápida |
| `auto` | 1 | ✅ | ✅ | **Padrão** — melhor equilíbrio |
| `deep_lite` | 3 | ✅ | ✅ | Pesquisa moderada |
| `deep` | 5 | ✅ | ✅ | Pesquisa completa |
| `deep_reasoning` | 7 | ✅ | ✅ | Investigação complexa |

**Categorias (`category`):**

| Categoria | Domínios priorizados |
|-----------|---------------------|
| `general` | Todos os motores |
| `news` | BBC, Reuters, AP News, NYT, Guardian |
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

### `site_search` — busca dentro de um domínio

Busca com `site:dominio query` — útil para encontrar documentação oficial ou conteúdo específico de uma fonte.

```python
site_search(
    query="async io concurrency",
    site="docs.python.org",
    time_range="year",   # opcional
    limit=5,             # padrão: 5
)
```

---

### `fetch_page` — extrair conteúdo de uma URL

Extrai o conteúdo em texto limpo de uma página web. Tenta `curl-cffi` (anti-bot), `nodriver` (browser headless) e `httpx` em fallback.

```python
fetch_page(
    url="https://docs.python.org/3/whatsnew/3.13.html",
    max_tokens=8000,   # opcional, padrão: 8000
)
```

Retorna: título, descrição, headings, conteúdo principal, tabelas, dados JSON-LD e resumo de links.

---

### `get_contents` — buscar conteúdo de múltiplas URLs

Faz fetch paralelo de até 20 URLs com concorrência controlada (máx. 3 simultâneos). Pode extrair highlights e resumos.

```python
get_contents(
    urls=[
        "https://arxiv.org/abs/2401.04012",
        "https://github.com/openai/gpt-2",
    ],
    highlight_query="large language model training",   # opcional
    highlight_sentences=3,                              # padrão: 3
    enable_summary=False,                               # padrão: False
    max_tokens=8000,                                    # por URL, padrão: 8000
)
```

---

### `answer` — resposta direta a partir de URLs

Faz fetch das URLs fornecidas, extrai os trechos mais relevantes para a pergunta e retorna uma resposta extrativa.

```python
answer(
    query="Qual é o tamanho máximo do contexto do Claude 3.5?",
    urls=["https://docs.anthropic.com/en/docs/about-claude/all-releases"],
)
```

---

## Tiers de autoridade de fonte

Todos os resultados são classificados em 4 tiers de confiabilidade:

| Tier | Emoji | Descrição | Exemplos |
|------|-------|-----------|----------|
| Tier 1 | 🟢 | Oficial / Definitivo | `github.com`, `docs.python.org`, `.gov`, `.edu` |
| Tier 2 | 🔵 | Autoritativo | `wikipedia.org`, `stackoverflow.com`, `arxiv.org` |
| Tier 3 | 🟡 | Referência | `medium.com`, `reuters.com`, `dev.to` |
| Tier 4 | ⚪ | Geral | Blogs genéricos, Reddit, SEO |

---

## Variáveis de ambiente

Todas as variáveis são configuradas no arquivo `.env`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEARXNG_HOST` | `http://searxng:8080` | URL interna do SearXNG |
| `SEARXNG_ENGINES` | `google,duckduckgo,bing,wikipedia,startpage` | Motores ativos (separados por vírgula) |
| `SEARXNG_DEFAULT_CATEGORY` | `general` | Categoria padrão quando não especificada |
| `SEARXNG_SAFESEARCH` | `0` | Nível de safe search: `0`, `1` ou `2` |
| `SEARXNG_SECRET` | *(obrigatório)* | Chave secreta do SearXNG — **troque antes de usar** |
| `SEARCH_DEFAULT_TYPE` | `auto` | Tipo de busca padrão: `instant`, `fast`, `auto`, `deep_lite`, `deep`, `deep_reasoning` |
| `SEARCH_DEFAULT_LIMIT` | `10` | Limite padrão de resultados (1–20) |
| `SEARCH_TIMEOUT_SECONDS` | `10` | Timeout de busca em segundos |
| `FETCH_TIMEOUT_SECONDS` | `15` | Timeout de fetch de página em segundos |
| `FETCH_MAX_CONTENT_LENGTH` | `10000` | Máximo de caracteres extraídos por página |
| `FETCH_TOKEN_BUDGET` | `8000` | Orçamento de tokens por página |
| `MCP_SERVER_HOST` | `0.0.0.0` | Host que o servidor MCP escuta |
| `MCP_SERVER_PORT` | `8000` | Porta do servidor MCP |
| `API_KEY` | *(vazio)* | Chave de API opcional para proteger o servidor |

---

## Estrutura do projeto

```
WIE_MCP/
├── src/
│   ├── server.py              # Servidor MCP — registra as 6 ferramentas
│   ├── config.py              # Configurações via Pydantic Settings + .env
│   ├── constants.py           # Tiers de domínio, tipos de busca, categorias
│   ├── models.py              # Schemas Pydantic (request/response)
│   ├── errors.py              # Classes de erro tipadas
│   ├── searxng_client.py      # Cliente HTTP para o SearXNG
│   ├── tools/
│   │   ├── web_search.py          # Ferramenta web_search
│   │   ├── web_search_advanced.py # Ferramenta web_search_advanced
│   │   ├── fetch_page.py          # Ferramenta fetch_page
│   │   ├── get_contents.py        # Ferramenta get_contents
│   │   ├── site_search.py         # Ferramenta site_search
│   │   └── answer.py              # Ferramenta answer
│   └── utils/
│       ├── dedup.py               # Deduplicação e pontuação de resultados
│       ├── highlights.py          # Extração de trechos relevantes
│       ├── summarizer.py          # Resumo extrativo
│       ├── text.py                # Divisor de sentenças
│       ├── query_expander.py      # Expansão de queries para modos deep
│       ├── readability.py         # Extração de conteúdo legível
│       └── truncation.py          # Truncamento por tokens
├── configs/
│   ├── claude-desktop.json    # Config para Claude Desktop (STDIO)
│   ├── cursor.json            # Config para Cursor (STDIO)
│   ├── zed.json               # Config para Zed (STDIO)
│   ├── windsurf.json          # Config para Windsurf (STDIO)
│   ├── vscode-cline.json      # Config para VS Code + Cline (STDIO)
│   ├── http-remote.json       # Config HTTP (Docker)
│   └── lm-studio.json         # Config para LM Studio (HTTP)
├── searxng/
│   └── settings.yml           # Configuração do SearXNG
├── docker-compose.yml         # Sobe wie-mcp-server + wie-searxng
├── Dockerfile                 # Imagem do servidor MCP
├── requirements.txt           # Dependências Python
├── .env.example               # Template de variáveis de ambiente
└── pytest.ini                 # Configuração de testes
```

---

## Dependências principais

| Pacote | Uso |
|--------|-----|
| `mcp` | Protocolo MCP (FastMCP) |
| `httpx` | Requisições HTTP assíncronas |
| `pydantic` + `pydantic-settings` | Validação e configuração |
| `beautifulsoup4` + `readability-lxml` | Parsing e extração de HTML |
| `curl-cffi` | Cliente HTTP com bypass de bot detection |
| `nodriver` | Browser headless como fallback |
| `flashrank` | Reranking local por relevância (opcional) |
| `uvicorn` + `starlette` | Servidor HTTP para modo Streamable HTTP |

---

## Comandos úteis

```bash
# Subir tudo
docker compose up -d

# Ver logs em tempo real
docker compose logs -f

# Parar tudo
docker compose down

# Reconstruir após mudanças no código
docker compose up -d --build

# Rodar testes
python -m pytest tests/ -v

# Rodar servidor localmente (STDIO)
python -m src.server stdio

# Rodar servidor localmente (HTTP)
python -m src.server http
```

---

## Resolução de problemas

### "Connection refused" ou "Cannot reach SearXNG"
- Verifique se os containers estão rodando: `docker ps`
- Aguarde ~30s após `docker compose up -d` para o SearXNG inicializar
- Verifique os logs: `docker logs wie-searxng`

### Sem resultados de busca
- O SearXNG pode estar com os engines configurados incorretamente
- Verifique `searxng/settings.yml` e se os engines estão ativos

### Porta já em uso
- Altere a porta no `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"   # usa porta 8001 no host
  ```
- E atualize a URL na configuração do cliente para `http://localhost:8001/mcp`

### Acesso de outra máquina
- Substitua `localhost` pelo IP da máquina que está rodando o Docker:
  ```json
  { "url": "http://192.168.1.100:8000/mcp" }
  ```

---

## Licença

**GNU Affero General Public License v3 (AGPLv3)** — [LICENSE](LICENSE)

Copyright © 2025–2026 Jonathan Lima