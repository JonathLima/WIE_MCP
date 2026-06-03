# src/utils/text.py
from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences on . ! ? boundaries."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
