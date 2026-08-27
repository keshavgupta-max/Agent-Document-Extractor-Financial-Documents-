"""Tests for BankStatementExtractor supporting heterogeneous column formats."""

from tools.extractor.extractors.bank_statement_extractor import BankStatementExtractor
from tools.parser.models import ParsedDocument, TableContent


def test_bank_statement_explicit_credit_debit_columns():
    """Verify extraction with explicit Credit and Debit columns."""
    table = TableContent(
        table_index=0,
        headers=["Date", "Description", "Debit", "Credit", "Balance"],
        rows=[
            ["2022-01-10", "Deposit from Client", "", "15000.00", "45000.00"],
            ["2022-01-12", "Office Supplies", "2500.00", "", "42500.00"],
            ["2022-01-15", "Consulting Fee", "", "10000.00", "52500.00"],
        ],
    )

    doc = ParsedDocument(
        document_id="doc_bs_1",
        storage_path="/tmp/bs1.csv",
        file_extension=".csv",
        mime_type="text/csv",
        page_count=0,
        pages=[],
        tables=[table],
        metadata={},
        parsing_status="SUCCESS",
    )

    extractor = BankStatementExtractor()
    result = extractor.extract(doc, "BANK_STATEMENT")

    assert result.additional_fields["total_credit_amount"] == "25000.00"
    assert result.additional_fields["total_debit_amount"] == "2500.00"
    assert result.additional_fields["total_transactions"] == 3
    assert result.additional_fields["opening_balance"] == "45000.00"
    assert result.additional_fields["closing_balance"] == "52500.00"


def test_bank_statement_type_direction_and_amount_columns():
    """Verify extraction with Type (Cr/Db) and Amount columns."""
    table = TableContent(
        table_index=0,
        headers=["Date", "Type", "Amount", "Balance", "Mode"],
        rows=[
            ["2022-01-12", "Cr", "1000.00", "452963.87", "UPI"],
            ["2022-01-29", "CR", "2400.00", "446258.96", "NEFT"],
            ["2022-02-05", "Db", "500.00", "445758.96", "ATM"],
            ["2022-02-10", "DR", "1500.00", "444258.96", "UPI"],
            ["2022-02-15", "UNKNOWN", "999.00", "444258.96", "POS"],
        ],
    )

    doc = ParsedDocument(
        document_id="doc_bs_2",
        storage_path="/tmp/bs2.csv",
        file_extension=".csv",
        mime_type="text/csv",
        page_count=0,
        pages=[],
        tables=[table],
        metadata={},
        parsing_status="SUCCESS",
    )

    extractor = BankStatementExtractor()
    result = extractor.extract(doc, "BANK_STATEMENT")

    assert result.additional_fields["total_credit_amount"] == "3400.00"
    assert result.additional_fields["total_debit_amount"] == "2000.00"
    assert result.additional_fields["total_transactions"] == 5
    assert len(result.line_items) == 5


def test_bank_statement_no_double_counting_when_both_present():
    """Verify priority prevents double counting if explicit and direction schemas coexist."""
    table = TableContent(
        table_index=0,
        headers=["Date", "Debit", "Credit", "Type", "Amount", "Balance"],
        rows=[
            ["2022-01-10", "", "5000.00", "Cr", "5000.00", "5000.00"],
            ["2022-01-12", "2000.00", "", "Dr", "2000.00", "3000.00"],
        ],
    )

    doc = ParsedDocument(
        document_id="doc_bs_3",
        storage_path="/tmp/bs3.csv",
        file_extension=".csv",
        mime_type="text/csv",
        page_count=0,
        pages=[],
        tables=[table],
        metadata={},
        parsing_status="SUCCESS",
    )

    extractor = BankStatementExtractor()
    result = extractor.extract(doc, "BANK_STATEMENT")

    assert result.additional_fields["total_credit_amount"] == "5000.00"
    assert result.additional_fields["total_debit_amount"] == "2000.00"