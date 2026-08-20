"""Utility functions for semantic text formatting and deterministic chunking."""

import uuid
from typing import List

from tools.embedding_prep.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    MINIMUM_CHUNK_SIZE,
)


def generate_chunk_id(document_id: str, chunk_index: int) -> str:
    """Generates a deterministic UUID for a chunk based on document ID and index."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # Standard DNS Namespace
    name_key = f"{document_id}_chunk_{chunk_index}"
    return str(uuid.uuid5(namespace, name_key))


def create_overlapping_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Splits a semantic text string into overlapping character chunks cleanly.

    Prefers breaking on paragraph (`\n\n`) or line breaks (`\n`) where possible.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    if len(cleaned_text) <= chunk_size:
        return [cleaned_text]

    chunks: List[str] = []
    start = 0
    text_len = len(cleaned_text)

    while start < text_len:
        end = start + chunk_size

        if end >= text_len:
            chunks.append(cleaned_text[start:].strip())
            break

        # Attempt to break at natural paragraph or line break
        break_pos = cleaned_text.rfind("\n\n", start, end)
        if break_pos == -1 or break_pos < start + MINIMUM_CHUNK_SIZE:
            break_pos = cleaned_text.rfind("\n", start, end)

        if break_pos == -1 or break_pos < start + MINIMUM_CHUNK_SIZE:
            break_pos = cleaned_text.rfind(" ", start, end)

        if break_pos == -1 or break_pos < start + MINIMUM_CHUNK_SIZE:
            break_pos = end

        chunk_str = cleaned_text[start:break_pos].strip()
        if chunk_str:
            chunks.append(chunk_str)

        # Move start pointer back by overlap amount
        start = max(start + 1, break_pos - chunk_overlap)

    return chunks