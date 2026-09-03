"""Tests verifying deterministic document attribution UUID sanitization."""

from unittest.mock import MagicMock
from tools.query.service import QueryService
from tools.query.models import QuerySourceChunk


def test_replace_attribution_patterns_single_doc():
    """Verify 'Document ID: <uuid>' pattern is replaced with 'Document: <filename>'."""
    service = QueryService(api_key="mock-key")
    doc_id = "934a9336-f2f4-46af-8c7a-7037221ff223"
    filename = "large_bank_statement_200_transactions.csv"

    raw_answer = f"According to Document ID: {doc_id}, total credits are 55,000.00."
    sanitized = service._replace_attribution_patterns(raw_answer, {doc_id: filename})

    assert f"Document: {filename}" in sanitized
    assert f"Document ID: {doc_id}" not in sanitized
    assert "total credits are 55,000.00." in sanitized


def test_replace_attribution_patterns_multiple_docs_and_whitespace():
    """Verify multiple IDs and 'Document ID <uuid>' patterns are replaced correctly."""
    service = QueryService(api_key="mock-key")
    doc_1 = "uuid-111-aaa"
    file_1 = "statement_jan.csv"
    doc_2 = "uuid-222-bbb"
    file_2 = "invoice_feb.pdf"

    raw_answer = f"Document ID {doc_1} has closing balance 1000. Document ID: {doc_2} subtotal is 500."
    sanitized = service._replace_attribution_patterns(raw_answer, {doc_1: file_1, doc_2: file_2})

    assert f"Document: {file_1} has closing balance 1000." in sanitized
    assert f"Document: {file_2} subtotal is 500." in sanitized


def test_replace_attribution_patterns_leaves_unrelated_text_and_missing_filename():
    """Verify unrelated text remains unchanged and missing filename safely falls back."""
    service = QueryService(api_key="mock-key")
    doc_id = "uuid-fallback-999"

    raw_answer = f"Document ID: {doc_id} has balance 200."
    # Missing filename (falls back to doc_id)
    sanitized = service._replace_attribution_patterns(raw_answer, {doc_id: doc_id})

    assert sanitized == raw_answer


def test_format_retrieved_context_preserves_query_source_chunk_identity():
    """Verify QuerySourceChunk retains the internal UUID while prompt context uses filename."""
    service = QueryService(api_key="mock-key")

    mock_chunk = MagicMock()
    mock_chunk.chunk_id = "chunk-101"
    mock_chunk.document_id = "doc-uuid-real-123"
    mock_chunk.workspace_id = "ws_test"
    mock_chunk.distance = 0.12
    mock_chunk.metadata.chunk_index = 0
    mock_chunk.metadata.document_type = "BANK_STATEMENT"
    mock_chunk.metadata.original_filename = "verified_statement.csv"
    mock_chunk.text_content = "Document ID: doc-uuid-real-123\nTotal Credit: 5000"

    context_block, sources, mapping = service._format_retrieved_context([mock_chunk])

    # Internal identity in QuerySourceChunk remains UNCHANGED
    assert len(sources) == 1
    assert isinstance(sources[0], QuerySourceChunk)
    assert sources[0].document_id == "doc-uuid-real-123"
    assert sources[0].chunk_id == "chunk-101"

    # Prompt context was sanitized
    assert "verified_statement.csv" in context_block
    assert "Document: verified_statement.csv" in context_block
    assert "doc-uuid-real-123" not in context_block