# WIE - Web Investigator Engine

> **Privacidade primeiro, ilimitado, busca neural sem custos para agentes AI**

[![Licença AGPLv3](https://img.shields.io/badge/Licen%C3%A7a-AGPLv3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)

Um servidor MCP (Model Context Protocol) de alta precisão que fornece ferramentas de investigação profunda para LLMs. Construído sobre o **Investigator Pattern**: metadados ricos e extração profunda de conteúdo permitem que modelos (Claude, Gemini, GPT-4) realizem pesquisas factualmente perfeitas — sem prompts complexos.

🇺🇸 [English version available here](./README.md)

---

## ✨ Por Que WIE - Web Investigator Engine?

| Recurso | Exa Search | WIE - Web Investigator Engine |
|---------|-----------|-------------------------------|
| **Custo** | Plano pago | Gratuito e open-source |
| **Privacidade** | Dados podem ser logados | Zero-logging, self-hosted |
| **Customização** | Limitada | Acesso total ao código |
| **Infraestrutura** | Dependência de API externa | Rode em seu próprio hardware |
| **Transparência** | Black box proprietária | Totalmente transparente |
| **Velocidade** | Rápido | Otimizado para eficiência de LLM |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MCP SERVER                                        │
│                     (Investigator Pattern)                                 │
│                                                                             │
│   ┌──────────────────┐  ┌───────────────────────┐  ┌──────────────────┐   │
│   │  web_search()    │  │ web_search_advanced()  │  │  site_search()   │   │
│   │  (Descoberta)   │  │  (Paridade Exa)     │  │  (Definitivo)   │   │
│   └──────────────────┘  └───────────────────────┘  └──────────────────┘   │
│                                                                             │
│   ┌──────────────────┐  ┌───────────────────────┐                          │
│   │  fetch_page()    │  │   get_contents()      │                          │
│   │  (Única URL)    │  │  (Lote + Highlights) │                          │
│   └──────────────────┘  └───────────────────────┘                          │
│                                                                             │
│   ┌───────────────────────┐                                                 │
│   │      answer()          │  (QA Extração)                                │
│   └───────────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAMADA BACKEND                                      │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │    SearxNG     │  │   FlashRank    │  │    Extração de Conteúdo    │  │
│  │  Multi-Motor   │  │  Reranking   │  │  curl_cffi → nodriver │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔎 Tipos de Busca

| Tipo | Descrição | Caso de Uso |
|------|-------------|----------|
| **`auto`** | Melhor geral — velocidade/qualidade equilibrada | Pesquisa geral, primeira descoberta |
| **`fast`** | Resultados instantâneos, processamento mínimo | Fatos rápidos, motor único |
| **`instant`** | Sub-segundo, resultados ultra-leves | "Estou com sorte" — só top 3 |
| **`deep-lite`** | Pesquisa profunda leve — 3 variações de query | Pesquisa de fundo, investigação inicial |
| **`deep`** | Pesquisa profunda completa — 5 variações de query | Relatórios completos, análise detalhada |
| **`deep-reasoning`** | Multi-step chain-of-thought — 7+ variações | Investigações complexas, síntese multi-perspectiva |

---

## ⚡ Velocidade vs Qualidade

Escolha o tipo de busca certo conforme sua necessidade de velocidade/qualidade:

| Tipo | Velocidade | Queries | Rerank | Melhor Para |
|------|------------|---------|--------|-------------|
| `instant` | ⚡⚡⚡ Muito rápida | 1 | Fatos rápidos, "Estou com sorte" |
| `fast` | ⚡⚡ Rápida | 1 | Busca geral rápida |
| `auto` | ⚡ Equilibrada | 1 | **Padrão** — recomendado |
| `deep_lite` | 🐢 Lenta | 3 | Pesquisa de fundo |
| `deep` | 🐢🐢 Mais lenta | 5 | Relatórios completos |
| `deep_reasoning` | 🐢🐢🐢 Mais lenta | 7+ | Investigações complexas |

### Configuração de Velocidade via .env

Para máxima velocidade, edite seu arquivo `.env`:

```bash
# Máxima velocidade (1 engine, 5s timeout, modo fast)
SEARXNG_ENGINES=google
SEARCH_TIMEOUT_SECONDS=5
SEARCH_DEFAULT_TYPE=fast
```

Para máxima qualidade, use modos deep nas chamadas:

```python
web_search_advanced({
    "query": "seu tópico",
    "type": "deep",  # or "deep_reasoning"
    "numResults": 20
})
```

---

## 📂 Categorias

Filtre resultados por tipo de conteúdo para pesquisas mais direcionadas:

| Categoria | Descrição | Melhor Para |
|----------|-------------|----------|
| **`general`** | Conteúdo web geral | Tópicos amplos |
| **`news`** | Artigos de notícias | Eventos atuais, notícias |
| **`research_paper`** | Artigos científicos, arxiv | Pesquisa acadêmica, citações |
| **`company`** | Sites de negócios, páginas corporativas | Perfis empresariais |
| **`people`** | Biografias, perfis, sociais | Busca de pessoas |
| **`financial_report`** | Arquivos SEC, relatórios, PDFs | Pesquisa de investimentos |
| **`product`** | Páginas de produtos, e-commerce | Especificações de produtos |
| **`personal_site`** | Blogs, portfólios, sites pessoais | Opiniões especializadas |
| **`code`** | GitHub, StackOverflow, docs | Exemplos de código, documentação |
| **`video`** | Conteúdo de vídeo | Tutoriais, demonstrações |
| **`image`** | Imagens e conteúdo visual | Referências visuais |

---

## 🛠️ Referência das Ferramentas

### `web_search` — Busca de Descoberta

Busca multi-motor básica com pontuação por tier de autoridade.

```python
{
  "query": "latest Python release 2025",
  "time_range": "day",        # hour, day, week, month, year
  "categories": "news",       # general, news, images, videos, it, science
  "safesearch": "0",          # 0=off, 1=moderate, 2=strict
  "limit": 10                 # 1-20 results
}
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `query` | `string` | **Obrigatório** | Query de busca |
| `time_range` | `string` | `null` | Filtro: `hour`, `day`, `week`, `month`, `year` |
| `categories` | `string` | `null` | Filtro de categoria |
| `safesearch` | `string` | `null` | Safe search: `0`, `1`, `2` |
| `limit` | `int` | `10` | Resultados 1-20 |

---

### `web_search_advanced` — Busca Avançada Estilo Exa

Busca completa com todas as opções de filtro, highlights e resumos.

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

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `query` | `string` | **Obrigatório** | Query de busca |
| `type` | `SearchType` | `"auto"` | Tipo: `auto`, `fast`, `instant`, `deep_lite`, `deep`, `deep_reasoning` |
| `numResults` | `int` | `10` | Resultados (1-100) |
| `category` | `Category` | `null` | Filtro de categoria |
| `includeDomains` | `list[string]` | `null` | Domínios obrigatórios |
| `excludeDomains` | `list[string]` | `null` | Domínios bloqueados |
| `startPublishedDate` | `string` | `null` | ISO — publicado após |
| `endPublishedDate` | `string` | `null` | ISO — publicado antes |
| `startCrawlDate` | `string` | `null` | ISO — rastreado após |
| `endCrawlDate` | `string` | `null` | ISO — rastreado antes |
| `includeText` | `list[string]` | `null` | Frases obrigatórias na página |
| `excludeText` | `list[string]` | `null` | Frases excluídas |
| `userLocation` | `object` | `null` | `{"country": "US", "city": "NYC"}` |
| `safesearch` | `int` | `0` | 0=off, 1=moderate, 2=strict |
| `enableHighlights` | `bool` | `true` | Incluir highlights da query |
| `highlight_sentences` | `int` | `3` | Sentenças por highlight (1-10) |
| `enableSummary` | `bool` | `false` | Incluir resumo extrativo |
| `additionalQueries` | `bool` | `true` | Habilitar expansão de query para modos deep |

---

### `get_contents` — Recuperação de Conteúdo em Lote

Busca múltiplas URLs simultaneamente com highlights e resumos.

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

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `urls` | `list[string]` | **Obrigatório** | URLs para buscar (1-20) |
| `highlight_query` | `string` | `null` | Query para extração de highlight |
| `highlight_sentences` | `int` | `3` | Sentenças por highlight |
| `enableSummary` | `bool` | `false` | Incluir resumo extrativo |
| `max_tokens` | `int` | `8000` | Orçamento de tokens por URL (500-128000) |

---

### `answer` — QA por Extração

Respostas diretas de documentos fonte.

```python
{
  "query": "What is the main contribution of this paper?",
  "urls": ["https://arxiv.org/abs/2401.04012"]
}
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `query` | `string` | **Obrigatório** | Pergunta a responder |
| `urls` | `list[string]` | **Obrigatório** | URLs fonte (1-20) |

---

### `site_search` — Busca de Verdade Definitiva

Busca dentro de um domínio específico para resultados autoritativos.

```python
{
  "query": "async io release notes",
  "site": "docs.python.org"
}
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `query` | `string` | **Obrigatório** | Query de busca |
| `site` | `string` | **Obrigatório** | Domínio alvo (ex: `github.com`, `docs.rs`) |

---

### `fetch_page` — Extração de Página Única

Extrai conteúdo limpo em markdown de uma única URL.

```python
{
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "max_tokens": 16000
}
```

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|---------|-------------|
| `url` | `string` | **Obrigatório** | URL completa |
| `max_tokens` | `int` | `null` | Orçamento de tokens (500-128000) |

---

## 🚀 Quick Start

### 1. Clonar e Configurar

```bash
git clone https://github.com/seu-usuario/SearchEngineLLM.git
cd SearchEngineLLM
cp .env.example .env
# Edite .env: mude SEARXNG_SECRET para um valor seguro
```

### 2. Iniciar com Docker

```bash
docker compose up -d
```

### 3. Configurar Seu Cliente MCP

Este servidor suporta ambos os transports: **STDIO** (local) e **Streamable HTTP** (remoto).

#### Modo STDIO

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

#### Modo HTTP (Remoto)

```bash
python -m src.server http
# Servidor roda em http://localhost:8000/mcp
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

## 💻 Configurações de Cliente

### Claude Desktop

**Arquivo:** `configs/claude_desktop.json`

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

Adicione em `~/Library/Application Support/Claude/claude_desktop_config.json`

---

### Cursor

**Arquivo:** `configs/cursor.json`

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

**Arquivo:** `configs/zed.json`

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

**Arquivo:** `configs/windsurf.json`

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

**Arquivo:** `configs/vscode-cline.json`

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

**Arquivo:** `configs/lm-studio.json`

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

## 📖 Exemplos de Uso

### Busca Básica

```
web_search({
  "query": "latest SpaceX Starship launch",
  "time_range": "day"
})
```

### Pesquisa Profunda Avançada

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

### Busca de Conteúdo em Lote com Highlights

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

### QA Extração

```
answer({
  "query": "What is the context window size for Claude 3.5?",
  "urls": ["https://docs.anthropic.com/en/docs/about-claude/all-releases"]
})
```

### Busca Específica por Domínio

```
site_search({
  "query": "async io concurrency",
  "site": "docs.python.org"
})
```

### Pesquisa por Categoria

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

## 🤖 Habilidades de Agente

Prompts prontos para investigação autônoma.

### Pesquisa Empresarial

```
Você é um pesquisador empresarial profissional. Investigue [NOME DA EMPRESA] usando a seguinte abordagem:

1. Use web_search_advanced com category="company" para encontrar fontes oficiais
2. Busque notícias recentes, relatórios financeiros e comunicados oficiais
3. Use get_contents para extrair informações detalhadas do site e press releases
4. Use answer para extrair fatos-chave sobre produtos, liderança e desenvolvimentos recentes
5. Compile as descobertas em um perfil empresarial completo com:
   - Visão geral e missão da empresa
   - Desempenho e notícias recentes
   - Liderança e pessoas-chave
   - Produtos ou serviços oferecidos
   - Posição financeira (se pública)
```

### Busca de Pessoas

```
Você é um investigador profissional especializado em busca de pessoas. Encontre informações completas sobre [NOME DA PESSOA] através de:

1. Use web_search_advanced com category="people" para fontes biográficas
2. Busque perfis profissionais (LinkedIn, Crunchbase), Wikipedia e sites pessoais
3. Use get_contents para extrair informações biográficas detalhadas
4. Use answer para extrair histórico de carreira, conquistas e fatos notáveis
5. Retorne um perfil detalhado incluindo:
   - Background profissional e carreira
   - Conquistas e contribuições notáveis
   - Afiliação atual
   - Formação educacional
```

### Investigação de Artigo Científico

```
Você é um pesquisador acadêmico. Realize uma investigação completa de [TÓPICO/ARTIGO] através de:

1. Use web_search_advanced com category="research_paper", mirando arxiv.org e bases acadêmicas
2. Busque título do artigo, autores e conceitos-chave
3. Use get_contents para extrair o conteúdo completo do artigo
4. Use answer para extrair:
   - Contribuição principal e inovações
   - Metodologia utilizada
   - Resultados e conclusões-chave
   - Limitações e trabalho futuro
5. Retorne um resumo acadêmico estruturado com citações
```

### Análise de Relatório Financeiro

```
Você é um analista financeiro. Analise relatórios financeiros de [EMPRESA/TÓPICO] através de:

1. Use web_search_advanced com category="financial_report" para encontrar arquivos SEC, relatórios
2. Busque relatórios anuais (10-K), trimestrais (10-Q) e apresentações para investidores
3. Use get_contents para extrair dados financeiros detalhados
4. Use answer para extrair métricas financeiras-chave, rácios e narrativa
5. Retorne um resumo financeiro com:
   - Tendências de receita e lucro
   - Rácios financeiros principais
   - Eventos ou mudanças significativas
   - Destaques e riscos de investimento
```

### Contexto de Código para Desenvolvimento

```
Você é um engenheiro de software sênior. Investigue [BIBLIOTECA/FRAMEWORK/API] para contexto de código através de:

1. Use web_search_advanced com category="code", mirando GitHub, StackOverflow e docs oficiais
2. Busque exemplos de uso, tutoriais e documentação da API
3. Use get_contents para extrair exemplos de código e documentação oficial
4. Use answer para extrair:
   - Assinaturas de API e parâmetros
   - Padrões de uso comuns
   - Melhores práticas e armadilhas
   - Informação de compatibilidade de versão
5. Retorne documentação completa de código com exemplos
```

### Investigação Profunda

```
Você é um investigador de pesquisa sênior. Realize uma investigação profunda de [TÓPICO COMPLEXO] usando chain-of-thought:

1. Use web_search_advanced com type="deep_reasoning" para análise multi-perspectiva completa
2. Gere múltiplas variações de query para explorar diferentes ângulos:
   - Background histórico e origens
   - Estado atual e desenvolvimentos recentes
   - Partes interessadas e perspectivas-chave
   - Controvérsias e debates
   - Implicações futuras e predições
3. Use get_contents para extrair informações detalhadas de fontes autoritativas
4. Use answer para sintetizar descobertas através de múltiplas fontes
5. Cruz-reference afirmações e identifique consenso vs. pontos disputados
6. Retorne um relatório de investigação completo com:
   - Resumo executivo
   - Descobertas detalhadas de cada perspectiva
   - Evidências e citações
   - Áreas de consenso e disputa
   - Implicações e recomendações
```

---

## 📊 Tiers de Autoridade

Resultados são classificados por confiabilidade da fonte:

| Tier | Descrição | Exemplos |
|------|-------------|----------|
| **🟢 Tier 1** | Definitivo / Oficial | `docs.python.org`, `github.com`, `.gov`, `.edu` |
| **🔵 Tier 2** | Autoritativo | Wikipedia, Stack Overflow, Arxiv |
| **🟡 Tier 3** | Referência | Tech blogs, News outlets, Publications |
| **⚪ Tier 4** | Outro | Reddit, Blogs genéricos, SEO |

---

## 📁 Estrutura do Projeto

```
SearchEngineLLM/
├── src/
│   ├── server.py                  # Ponto de entrada do servidor MCP
│   ├── config.py                  # Configurações Pydantic
│   ├── models.py                  # Schemas de request/response
│   ├── errors.py                  # Classes de erro
│   └── tools/
│       ├── web_search.py          # Busca de descoberta básica
│       ├── web_search_advanced.py # Busca avançada completa estilo Exa
│       ├── web_fetch.py           # Extração de conteúdo de URL única
│       ├── get_contents.py         # Conteúdo em lote + highlights
│       ├── site_search.py          # Busca por domínio específico
│       └── answer.py               # QA extração
├── configs/                        # Configurações de clientes MCP
├── docs/
│   └── superpowers/
│       └── specs/                 # Especificações de design
├── docker-compose.yml             # Docker Compose (MCP + SearxNG)
├── Dockerfile                     # Definição do container
├── requirements.txt              # Dependências Python
└── .env.example               # Template de ambiente
```

---

## 🐳 Deploy Docker

```bash
# Iniciar todos os serviços
docker compose up -d

# Ver logs
docker compose logs -f

# Parar serviços
docker compose down
```

Serviços:
- **wie-mcp-server**: Servidor MCP WIE na porta 8000
- **wie-searxng**: Meta-motor de busca na porta 8080

---

## 🔒 Segurança

- **Proteção SSRF**: Validação DNS, bloqueio de IPs privados
- **Validação de URL**: Scheme e netloc obrigatórios
- **Middleware de API key**: Auth Bearer token opcional
- **Zero logging**: Dados de usuários não são armazenados ou logados

---

## 📜 Licença

**GNU Affero General Public License v3 (AGPLv3)** — [LICENSE](LICENSE)

Copyright (C) 2025-2026 Jonathan Lima

---

## 🔧 Troubleshooting

### "Connection refused"
- Verifique se o container está rodando: `docker ps`
- Verifique logs: `docker logs wie-mcp-server`

### "Timeout"
- Use a URL `/mcp` (Streamable HTTP), não `/sse`

### "Invalid params"
- Verifique se a URL está correta: deve terminar em `/mcp`

### Acesso Remoto

Para acessar de outro computador, substitua `localhost` pelo IP do host:

```json
{
  "mcpServers": {
    "investigator": {
      "url": "http://192.168.1.100:8000/mcp"
    }
  }
}
```

### Variáveis de Ambiente

O WIE_MCP suporta variáveis de ambiente padrão configuradas via ambiente do sistema ou através de um arquivo `.env`:

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `SEARXNG_HOST` | Endereço do host do motor de busca SearxNG | `http://searxng:8080` |
| `SEARXNG_ENGINES` | Motores de busca ativados no SearxNG (separados por vírgula) | `google,duckduckgo,bing,wikipedia,startpage` |
| `SEARXNG_DEFAULT_CATEGORY` | Categoria de busca padrão | `general` |
| `SEARXNG_SAFESEARCH` | Nível do Safe Search: `0` (desativado), `1` (moderado), `2` (estrito) | `0` |
| `SEARCH_DEFAULT_TYPE` | Modo de busca padrão: `instant`, `fast`, `auto`, `deep_lite`, `deep`, `deep_reasoning` | `auto` |
| `SEARCH_DEFAULT_LIMIT` | Limite padrão de resultados retornados pela busca de descoberta | `10` |
| `SEARCH_TIMEOUT_SECONDS` | Timeout da busca em segundos | `10.0` |
| `FETCH_TIMEOUT_SECONDS` | Timeout em segundos para busca e raspagem de páginas web | `15.0` |
| `FETCH_MAX_CONTENT_LENGTH` | Limite máximo de caracteres extraídos de uma página web | `10000` |
| `FETCH_TOKEN_BUDGET` | Orçamento aproximado de tokens do conteúdo extraído de páginas | `8000` |
| `MCP_SERVER_HOST` | Endereço de host que o servidor MCP escutará | `0.0.0.0` |
| `MCP_SERVER_PORT` | Porta de rede para o endpoint do servidor MCP | `8000` |
| `API_KEY` | Chave de API opcional para restringir o acesso ao servidor | *(nenhum)* |

### Porta Customizada

Para mudar a porta (ex: 8090):

```yaml
# docker-compose.yml
ports:
  - "8090:8000"

# Configuração do cliente
"url": "http://localhost:8090/mcp"
```