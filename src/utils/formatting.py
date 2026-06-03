"""Shared formatting utilities for MCP tool error responses."""
from __future__ import annotations

from src.models import ToolErrorResponse


def format_tool_error(
    error_code: str,
    message: str,
    retry_guidance: str,
) -> str:
    """Build a ToolErrorResponse and return its formatted markdown.

    This is the single source of truth for how tool errors are presented
    to the LLM client.  Every tool should call this instead of manually
    assembling the markdown string.
    """
    lines = [
        f"## ⚠️ Error: `{error_code}`",
        "",
        f"**{message}**",
        "",
        f"**How to proceed:** {retry_guidance}",
        "",
    ]
    return "\n".join(lines)
