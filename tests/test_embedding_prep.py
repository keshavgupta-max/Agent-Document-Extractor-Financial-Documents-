from tools.parser.models import ParsedDocument, PageContent
from tools.extractor.models import (
    StructuredBusinessDocument,
    HeaderFields,
    ExtractionMetadata,
)
from tools.embedding_prep.models import EmbeddingPrepInput
from tools.embedding_prep.service import EmbeddingPrepService
def test_embedding_prep_with_parsed_pages_appends_raw_lines_correctly():
    """Verify that documents containing parsed pages complete embedding preparation without TypeError."""
    parsed_doc = ParsedDocument(
        document_id="doc_page_test_001",
        storage_path="/tmp/test_invoice.pdf",
        file_extension=".pdf",
        mime_type="application/pdf",
        page_count=1,
        pages=[PageContent(page_number=1, text="INVOICE #INV-2026-001\nTotal: 5000 USD")],
        tables=[],
        metadata={},
        parsing_status="SUCCESS",
    )

    struct_doc = StructuredBusinessDocument(
        document_id="doc_page_test_001",
        header=HeaderFields(invoice_number="INV-2026-001"),
        metadata=ExtractionMetadata(document_type="INVOICE"),
    )

    prep_input = EmbeddingPrepInput(
        workspace_id="ws_test_pages",
        structured_document=struct_doc,
        parsed_document=parsed_doc,
        is_valid=True,
    )

    service = EmbeddingPrepService()
    result = service.prepare_document(prep_input)

    assert result.metadata.total_chunks >= 1
    assert "=== EXTRACTED PAGE TEXT ===" in result.full_semantic_text
    assert "[Page 1]\nINVOICE #INV-2026-001\nTotal: 5000 USD" in result.full_semantic_text