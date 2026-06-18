from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 4

def estimate_token_count(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)

def smart_truncate(
    content: str,
    token_budget: int,
    preserve_sections: bool = True,
) -> tuple[str, bool]:
    current_tokens = estimate_token_count(content)

    if current_tokens <= token_budget:
        return content, False

    char_budget = token_budget * CHARS_PER_TOKEN

    logger.info(
        "Truncating content: %d tokens → budget %d tokens (~%d chars)",
        current_tokens,
        token_budget,
        char_budget,
    )

    if preserve_sections:
        search_end = min(char_budget, len(content))
        break_pos = content.rfind("\n\n", 0, search_end)
        if break_pos > char_budget * 0.5:
            truncated = content[:break_pos]
            remaining_tokens = estimate_token_count(truncated)
            if remaining_tokens <= token_budget:
                truncated += "\n\n---\n*Content truncated to fit context window. "
                truncated += f"Original content was approximately {current_tokens} tokens.*"
                return truncated, True

    truncated = content[:char_budget]

    last_space = truncated.rfind(" ")
    if last_space > char_budget * 0.95:
        truncated = truncated[:last_space]

    truncated += "\n\n---\n*Content truncated to fit context window. "
    truncated += f"Original content was approximately {current_tokens} tokens.*"

    return truncated, True

def truncate_with_priority(
    content: str,
    token_budget: int,
    priority_patterns: list[str] | None = None,
) -> tuple[str, bool]:
    if priority_patterns is None:
        priority_patterns = [
            r"\n\| .+ \|",       # Markdown tables
            r"```[\s\S]*?```",   # Code blocks
            r"\n- .+",           # Bullet lists
            r"\n\d+\. .+",       # Numbered lists
            r"\n> .+",           # Blockquotes
        ]

    current_tokens = estimate_token_count(content)
    if current_tokens <= token_budget:
        return content, False

    priority_regions: list[tuple[int, int]] = []
    for pattern in priority_patterns:
        for match in re.finditer(pattern, content):
            priority_regions.append((match.start(), match.end()))

    if not priority_regions:
        return smart_truncate(content, token_budget)

    priority_regions.sort()
    merged: list[tuple[int, int]] = []
    for start, end in priority_regions:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    priority_tokens = estimate_token_count(content[priority_regions[0][0] : priority_regions[-1][1]] if priority_regions else "")

    if priority_tokens > token_budget:
        return smart_truncate(content, token_budget)

    remaining_budget = token_budget - priority_tokens
    remaining_chars = remaining_budget * CHARS_PER_TOKEN

    if merged:
        first_priority_start = merged[0][0]
        intro = content[: min(first_priority_start, remaining_chars)]
    else:
        intro = content[:remaining_chars]

    parts: list[str] = []
    if intro.strip():
        parts.append(intro.strip())

    for start, end in merged:
        parts.append(content[start:end])

    result = "\n\n".join(parts)
    result += "\n\n---\n*Content truncated to preserve structured data. "
    result += f"Some intermediate content was removed (original ~{current_tokens} tokens).*"

    return result, True


MAX_RESPONSE_CHARS = 16_000  # ~4K tokens — hard safety net for all tool responses

def cap_response(text: str, max_chars: int = MAX_RESPONSE_CHARS) -> str:
    """Hard cap on tool response size to prevent context window exhaustion.

    Every MCP tool must call this before returning its final string.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_break = truncated.rfind("\n\n")
    if last_break > max_chars * 0.8:
        truncated = truncated[:last_break]
    truncated += "\n\n---\n*Response truncated to fit context window.*"
    return truncated
