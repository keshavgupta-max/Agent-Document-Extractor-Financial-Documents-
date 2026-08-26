"""Focused unit and regression tests for BankStatementExtractor and downstream Embedding Preparation."""

import pytest
from tools.extractor.extractors.bank_statement_extractor import BankStatementExtractor
from tools.embedding_prep.models import EmbeddingPrepInput
from tools.embedding_prep.service import EmbeddingPrepService
from tools.parser.models import ParsedDocument, TableContent


def test_bank_statement_extractor_computes_aggregates_and_preserves_headers():
    """Verify headers preservation, debit/credit/balance calculation, and transaction count."""
    headers = ["Date", "Description", "Ref No", "Debit", "Credit", "Balance"]
    rows = [
        ["2026-01-02", "UPI/123/Vendor", "REF001", "", "5,000.00", "25,000.00"],
        ["2026-01-03", "ATM Withdrawal", "REF002", "2,000.00", "", "23,000.00"],
        ["2026-01-04", "Salary Deposit", "REF003", "", "50,000.00", "73,000.00"],
        ["2026-01-05", "Utility Bill", "REF004", "1,500.50", "", "71,499.50"],
    ]

    parsed_doc = ParsedDocument(
        document_id="doc_bank_agg_001",
        storage_path="/tmp/statement.csv",
        file_extension=".csv",
        mime_type="text/csv",
        page_count=1,
        pages=[],
        tables=[TableContent(table_index=0, headers=headers, rows=rows)],
        metadata={},
        parsing_status="SUCCESS",
    )

    extractor = BankStatementExtractor()
    result = extractor.extract(parsed_doc, "BANK_STATEMENT")

    # Header preservation
    assert len(result.line_items) == 4
    assert "Credit: 5,000.00" in result.line_items[0].description
    assert "Debit: 2,000.00" in result.line_items[1].description

    # Aggregate verification
    assert result.additional_fields["total_credit_amount"] == "55000.00"
    assert result.additional_fields["total_debit_amount"] == "3500.50"
    assert result.additional_fields["total_transactions"] == 4
    assert result.additional_fields["opening_balance"] == "25,000.00"
    assert result.additional_fields["closing_balance"] == "71,499.50"


def test_bank_statement_aggregates_rendered_in_embedding_prep():
    """Verify that computed statement aggregates appear in semantic text and chunk 0."""
    headers = ["Date", "Description", "Debit", "Credit", "Balance"]
    rows = [
        ["2026-01-02", "Client Payment", "", "10000.00", "10000.00"],
        ["2026-01-03", "Server Cost", "1500.00", "", "8500.00"],
    ]

    parsed_doc = ParsedDocument(
        document_id="doc_bank_prep_001",
        storage_path="/tmp/statement.csv",
        file_extension=".csv",
        mime_type="text/csv",
        page_count=1,
        pages=[],
        tables=[TableContent(table_index=0, headers=headers, rows=rows)],
        metadata={},
        parsing_status="SUCCESS",
    )

    extractor = BankStatementExtractor()
    structured_doc = extractor.extract(parsed_doc, "BANK_STATEMENT")

    prep_service = EmbeddingPrepService()
    prep_input = EmbeddingPrepInput(
        workspace_id="ws_bank_test",
        structured_document=structured_doc,
        parsed_document=parsed_doc,
        is_valid=True,
    )

    prepared_content = prep_service.prepare_document(prep_input)

    # Verify aggregates are present in the full semantic text
    assert "Total Credit Amount: 10000.00" in prepared_content.full_semantic_text
    assert "Total Debit Amount: 1500.00" in prepared_content.full_semantic_text
    assert "Total Transactions: 2" in prepared_content.full_semantic_text

    # Verify chunk 0 contains the aggregates
    chunk_0 = prepared_content.chunks[0]
    assert "Total Credit Amount: 10000.00" in chunk_0.text_content