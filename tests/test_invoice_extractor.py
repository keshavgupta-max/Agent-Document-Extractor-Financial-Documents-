"""Unit regression test for InvoiceExtractor tax extraction and total keyword collision."""

import pytest
from tools.extractor.extractors.invoice_extractor import InvoiceExtractor
from tools.parser.models import PageContent, ParsedDocument


def test_invoice_extractor_subtotal_total_and_tax_extraction():
    """Verify that 'TOTAL' keyword does not match 'SUBTOTAL' line and taxes are extracted."""
    invoice_text = (
        "INVOICE NO: INV-2026-001\n"
        "DATE: 2026-08-20\n"
        "SUBTOTAL: 102000.00\n"
        "CGST: 9180.00\n"
        "SGST: 9180.00\n"
        "TOTAL: 120360.00\n"
    )

    parsed_doc = ParsedDocument(
        document_id="doc_inv_test_001",
        storage_path="/tmp/invoice_test.pdf",
        file_extension=".pdf",
        mime_type="application/pdf",
        page_count=1,
        pages=[PageContent(page_number=1, text=invoice_text)],
        tables=[],
        metadata={},
        parsing_status="SUCCESS",
    )

    extractor = InvoiceExtractor()
    result = extractor.extract(parsed_doc, "INVOICE")

    # Totals verification
    assert result.totals.subtotal == "102000.00"
    assert result.totals.grand_total == "120360.00"
    assert result.totals.tax_amount == "18360.00"

    # Tax breakdowns verification
    assert result.taxes.cgst == "9180.00"
    assert result.taxes.sgst == "9180.00"
    assert result.taxes.igst is None
    assert result.taxes.total_tax == "18360.00"