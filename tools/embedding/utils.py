"""Utility functions for vector processing and validation in Phase 11."""

from typing import List

from tools.embedding.exceptions import EmbeddingDimensionMismatchError


def validate_vector_dimensions(vector: List[float], expected_dimensions: int) -> None:
    """Validates that a generated embedding vector meets the required dimensionality.

    Raises:
        EmbeddingDimensionMismatchError: If the vector length does not match expected_dimensions.
    """
    if not vector:
        raise EmbeddingDimensionMismatchError("Generated embedding vector is empty or None.")

    actual_dim = len(vector)
    if actual_dim != expected_dimensions:
        raise EmbeddingDimensionMismatchError(
            f"Vector dimension mismatch: expected {expected_dimensions}, got {actual_dim}."
        )


def truncate_text_for_embedding(text: str, max_chars: int = 8000) -> str:
    """Ensures input chunk text does not exceed provider context token/character limits."""
    cleaned = text.strip() if text else ""
    if len(cleaned) > max_chars:
        return cleaned[:max_chars]
    return cleaned