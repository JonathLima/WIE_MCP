from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

# === New Enums ===
class SearchType(str, Enum):
    AUTO = "auto"
    FAST = "fast"
    INSTANT = "instant"
    DEEP_LITE = "deep_lite"
    DEEP = "deep"
    DEEP_REASONING = "deep_reasoning"

class SearchCategory(str, Enum):
    GENERAL = "general"
    NEWS = "news"
    RESEARCH_PAPER = "research_paper"
    COMPANY = "company"
    PEOPLE = "people"
    FINANCIAL_REPORT = "financial_report"
    PRODUCT = "product"
    PERSONAL_SITE = "personal_site"
    CODE = "code"
    VIDEO = "video"
    IMAGE = "image"

# === Advanced Search Models ===
class UserLocation(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None

class SearchRequestAdvanced(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    search_type: SearchType = Field(default=SearchType.AUTO)
    num_results: int = Field(default=10, ge=1, le=100)
    category: Optional[SearchCategory] = None
    include_domains: Optional[list[str]] = None
    exclude_domains: Optional[list[str]] = None
    start_published_date: Optional[str] = None
    end_published_date: Optional[str] = None
    start_crawl_date: Optional[str] = None
    end_crawl_date: Optional[str] = None
    include_text: Optional[list[str]] = None
    exclude_text: Optional[list[str]] = None
    user_location: Optional[UserLocation] = None
    safesearch: Optional[int] = Field(default=0, ge=0, le=2)
    enable_highlights: bool = Field(default=True)
    highlight_sentences: int = Field(default=3, ge=1, le=10)
    enable_summary: bool = Field(default=False)
    additional_queries: bool = Field(default=True)

class SearchResultAdvanced(BaseModel):
    title: str
    url: HttpUrl
    snippet: str = ""
    published_date: Optional[str] = None
    author: Optional[str] = None
    domain: str = ""
    domain_tier: int = Field(ge=1, le=4)
    score: float = Field(ge=0.0)
    highlights: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    word_count: int = 0

class SearchResponseAdvanced(BaseModel):
    query: str
    results: list[SearchResultAdvanced]
    search_type: str
    total_found: int
    additional_queries_used: list[str] = Field(default_factory=list)
    incomplete_results: bool = False

# === Get Contents Models ===
class GetContentsRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=20)
    highlight_query: Optional[str] = None
    highlight_sentences: int = Field(default=3, ge=1, le=10)
    enable_summary: bool = Field(default=False)
    max_tokens: int = Field(default=8000, ge=500, le=128000)

class ContentItem(BaseModel):
    url: str
    status_code: int = 200
    title: str = ""
    author: Optional[str] = None
    published_date: Optional[str] = None
    word_count: int = 0
    content: str = ""
    highlights: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    raw: Optional[str] = None

class GetContentsResponse(BaseModel):
    contents: list[ContentItem]

# === Answer Models ===
class AnswerRequest(BaseModel):
    query: str = Field(min_length=1)
    urls: list[str] = Field(min_length=1, max_length=20)

class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]


class SearchRequest(BaseModel):

    query: str = Field(
        min_length=1,
        max_length=500,
        description="The search query string",
        examples=["latest Python release", "SpaceX Starship launch 2025"],
    )
    time_range: Optional[str] = Field(
        default=None,
        description="Filter results by time: hour, day, week, month, year",
        examples=["day", "week"],
    )
    categories: Optional[str] = Field(
        default=None,
        description="Search category: general, news, images, videos, it, science",
        examples=["news", "it"],
    )
    safesearch: Optional[str] = Field(
        default=None,
        description="Safe search level: 0=off, 1=moderate, 2=strict",
        examples=["0", "1"],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of results to return (1-20)",
    )

class SearchResult(BaseModel):

    id: int = Field(default=0, description="Unique identifier for reranking")
    title: str = Field(description="Page title")
    url: HttpUrl = Field(description="Result URL")
    snippet: str = Field(default="", description="Content snippet / summary")
    score: float = Field(
        default=1.0,
        ge=0.0,
        description="Composite relevance/reliability score (higher = better)",
    )
    engine: str = Field(default="", description="Engine that returned this result")
    published_date: Optional[str] = Field(
        default=None,
        description="Publication date if available from the engine",
    )
    has_specific_data: bool = Field(
        default=False,
        description="True if snippet contains specific data (versions, dates, prices)",
    )
    vagueness_detected: bool = Field(
        default=False,
        description="True if snippet contains vague language (approximately, around, etc.)",
    )
    domain_tier: int = Field(
        default=4,
        ge=1,
        le=4,
        description="Source authority tier: 1=official/definitive, 2=authoritative, 3=reference, 4=other",
    )

    @property
    def url_str(self) -> str:
        return str(self.url)

class SearchResponse(BaseModel):

    query: str = Field(description="The original search query")
    results: list[SearchResult] = Field(
        default_factory=list,
        description="List of search results sorted by score",
    )
    total_found: int = Field(default=0, description="Total results before dedup")
    engines_used: list[str] = Field(
        default_factory=list,
        description="List of engines queried",
    )
    markdown: str = Field(description="Formatted markdown for the LLM")

class FetchRequest(BaseModel):

    url: HttpUrl = Field(
        description="The full URL of the page to fetch and scrape",
        examples=["https://example.com/article", "https://docs.python.org/3/whatsnew/3.12.html"],
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=500,
        le=128000,
        description="Optional token budget override for this fetch",
    )

class TableData(BaseModel):

    headers: list[str] = Field(default_factory=list, description="Table header row")
    rows: list[list[str]] = Field(default_factory=list, description="Table data rows")

class LinkSummary(BaseModel):

    internal_count: int = Field(default=0, description="Number of internal links")
    external_count: int = Field(default=0, description="Number of external links")

class StructuredData(BaseModel):

    type: str = Field(default="", description="Schema.org type or context")
    data: dict = Field(default_factory=dict, description="Parsed JSON-LD data")

class FetchResponse(BaseModel):

    url: str = Field(description="The URL that was fetched")
    status_code: int = Field(default=200, description="HTTP status code")
    content_type: str = Field(default="", description="Response Content-Type header")

    title: str = Field(default="", description="Page title")
    description: str = Field(default="", description="Meta description")
    headings: list[dict[str, str]] = Field(
        default_factory=list,
        description="Page headings as [{level, text}, ...]",
    )
    content: str = Field(default="", description="Main article/content text")
    tables: list[TableData] = Field(
        default_factory=list,
        description="HTML tables extracted from the page",
    )
    structured_data: list[StructuredData] = Field(
        default_factory=list,
        description="JSON-LD structured data blocks",
    )
    links: LinkSummary = Field(
        default_factory=LinkSummary,
        description="Summary of internal/external links",
    )

    was_truncated: bool = Field(
        default=False,
        description="Whether content was truncated due to size",
    )
    markdown: str = Field(description="Formatted markdown for the LLM")

class ToolErrorResponse(BaseModel):

    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    retry_guidance: str = Field(
        description="Actionable guidance for the LLM to retry or work around the error",
    )
    markdown: str = Field(description="Formatted error as markdown for display")
