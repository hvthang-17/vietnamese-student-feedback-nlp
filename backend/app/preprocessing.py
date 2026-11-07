from __future__ import annotations

import re
import unicodedata
from typing import TypedDict


class ProcessedFeedback(TypedDict):
    raw_text: str
    normalized_text: str


def preprocess_text(text: str) -> ProcessedFeedback:
    """Validate and normalize Vietnamese feedback text.

    - Validates that the input is a valid non-empty string.
    - Normalizes Unicode composition to NFC (canonical for Vietnamese).
    - Collapses excessive whitespace characters into single spaces and strips margins.
    - Preserves all Vietnamese diacritics, casing, and punctuation.
    - Returns both the untouched original raw text and the normalized text.
    """
    if not isinstance(text, str):
        raise ValueError("Văn bản phải là chuỗi.")

    # Preserve exact raw text
    raw_text = text

    # Unicode NFC normalization (handles decomposed Vietnamese diacritics)
    nfc_text = unicodedata.normalize("NFC", raw_text)

    # Collapse any sequences of whitespace (\s+, tabs, newlines) to a single space and trim
    normalized = re.sub(r"\s+", " ", nfc_text).strip()

    if not normalized:
        raise ValueError("Nội dung phản hồi không được để trống.")

    return {
        "raw_text": raw_text,
        "normalized_text": normalized,
    }


def normalize_text(text: str) -> str:
    """Convenience helper returning just the normalized string."""
    return preprocess_text(text)["normalized_text"]
