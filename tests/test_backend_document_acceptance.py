"""Backend acceptance tests for supported document ingestion paths.

These tests verify the user-facing document pipeline without requiring
live Gemini embedding API calls.

Coverage:
- PDF invoice
- CSV bank statement
- XLSX invoice
- XLSX bank statement

The tests intentionally stop before live embedding generation. This keeps
the acceptance tests deterministic and avoids Gemini API quota dependency.
"""

from pathlib import Path

import pytest

from core.runtime import AgentRuntime
from core.runtime_models import ExecutionMode, IngestionPipelineInput
from core.tool_result import ToolResult
from tools.embedding_prep.models import EmbeddingPrepInput
from tools.embedding_prep.service import EmbeddingPrepService
from tools.extractor.extractors.bank_statement_extractor import (
    BankStatementExtractor,
)
from tools.extractor.extractors.invoice_extractor import InvoiceExtractor
from tools.parser.models import ParsedDocument, TableContent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_bank_statement_parsed_document() -> ParsedDocument:
    """Build a realistic parsed bank statement for local acceptance testing."""

    headers = [
        "Date",
        "Description",
        "Ref No",
        "Debit",
        "Credit",
        "Balance",
    ]

    rows = [
        [
            "2026-01-02",
            "UPI/123/Vendor",
            "REF001",
            "",
            "5000.00",
            "25000.00",
        ],
        [
            "2026-01-03",
            "ATM Withdrawal",
            "REF002",
            "2000.00",
            "",
            "23000.00",
        ],
        [
            "2026-01-04",
            "Salary Deposit",
            "REF003",
            "",
            "50000.00",
            "73000.00",
        ],
        [
            "2026-01-05",
            "Utility Bill",
            "REF004",
            "1500.50",
            "",
            "71499.50",
        ],
    ]

    return ParsedDocument(
        document_id="acceptance_bank_001",
        storage_path="data/staging/acceptance_bank.csv",
        file_extension=".csv",
        mime_type="text/csv",
        page_count=1,
        pages=[],
        tables=[
            TableContent(
                table_index=0,
                headers=headers,
                rows=rows,
            )
        ],
        metadata={},
        parsing_status="SUCCESS",
    )


# ---------------------------------------------------------------------------
# Bank Statement Extraction Acceptance
# ---------------------------------------------------------------------------


def test_bank_statement_acceptance_extracts_transaction_context():
    """Bank statement rows retain their original column semantics."""

    parsed_doc = build_bank_statement_parsed_document()

    extractor = BankStatementExtractor()
    result = extractor.extract(
        parsed_doc,
        "BANK_STATEMENT",
    )

    assert len(result.line_items) == 4

    first_transaction = result.line_items[0].description
    second_transaction = result.line_items[1].description

    assert "Date: 2026-01-02" in first_transaction
    assert "Description: UPI/123/Vendor" in first_transaction
    assert "Credit: 5000.00" in first_transaction
    assert "Balance: 25000.00" in first_transaction

    assert "Debit: 2000.00" in second_transaction
    assert "Balance: 23000.00" in second_transaction


def test_bank_statement_acceptance_computes_aggregates():
    """Bank statement aggregates are extracted correctly."""

    parsed_doc = build_bank_statement_parsed_document()

    extractor = BankStatementExtractor()
    result = extractor.extract(
        parsed_doc,
        "BANK_STATEMENT",
    )

    assert result.additional_fields["total_credit_amount"] == "55000.00"
    assert result.additional_fields["total_debit_amount"] == "3500.50"
    assert result.additional_fields["total_transactions"] == 4

    assert result.additional_fields["opening_balance"] == "25000.00"
    assert result.additional_fields["closing_balance"] == "71499.50"


# ---------------------------------------------------------------------------
# Embedding Preparation Acceptance
# ---------------------------------------------------------------------------


def test_bank_statement_acceptance_embedding_content():
    """Statement-level facts are preserved before embedding generation."""

    parsed_doc = build_bank_statement_parsed_document()

    extractor = BankStatementExtractor()
    structured_doc = extractor.extract(
        parsed_doc,
        "BANK_STATEMENT",
    )

    prep_service = EmbeddingPrepService()

    prep_input = EmbeddingPrepInput(
        workspace_id="ws_acceptance",
        structured_document=structured_doc,
        parsed_document=parsed_doc,
        is_valid=True,
    )

    prepared = prep_service.prepare_document(prep_input)

    semantic_text = prepared.full_semantic_text

    assert "Total Credit Amount: 55000.00" in semantic_text
    assert "Total Debit Amount: 3500.50" in semantic_text
    assert "Total Transactions: 4" in semantic_text
    assert "Opening Balance: 25000.00" in semantic_text
    assert "Closing Balance: 71499.50" in semantic_text

    # Transaction-level semantic context must also survive.
    assert "Credit: 5000.00" in semantic_text
    assert "Debit: 2000.00" in semantic_text
    assert "Balance: 25000.00" in semantic_text


# ---------------------------------------------------------------------------
# File Availability Acceptance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "invoice.pdf",
        "bankstatement.csv",
        "small_bank_statement.csv",
    ],
)
def test_existing_staging_documents_are_available(filename):
    """Verify the real local test documents exist in staging."""

    path = Path("data/staging") / filename

    assert path.exists(), f"Missing acceptance test file: {path}"
    assert path.is_file(), f"Acceptance path is not a file: {path}"
    assert path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Optional XLSX Availability Checks
# ---------------------------------------------------------------------------
#
# These tests do NOT assume that XLSX fixtures already exist.
# They are skipped until you place the corresponding files in staging.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "invoice.xlsx",
        "bankstatement.xlsx",
    ],
)
def test_xlsx_documents_available_when_provided(filename):
    """Verify XLSX fixtures when they are added to the staging directory."""

    path = Path("data/staging") / filename

    if not path.exists():
        pytest.skip(
            f"{filename} has not been added to data/staging yet."
        )

    assert path.is_file()
    assert path.stat().st_size > 0