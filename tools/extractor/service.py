"""Extractor Service routing documents to concrete family extractors."""

import time
from logger import logger
from tools.classifier.constants import DocumentType
from tools.extractor.exceptions import ExtractorExecutionError
from tools.extractor.extractors import (
    BankStatementExtractor,
    GenericExtractor,
    InvoiceExtractor,
    PurchaseOrderExtractor,
    ReceiptExtractor,
    SalarySlipExtractor,
)
from tools.extractor.models import ExtractorInput, StructuredBusinessDocument


class ExtractorService:
    """Service orchestrating extraction routing based on document classification."""

    def __init__(self) -> None:
        self._invoice_extractor = InvoiceExtractor()
        self._po_extractor = PurchaseOrderExtractor()
        self._bank_extractor = BankStatementExtractor()
        self._receipt_extractor = ReceiptExtractor()
        self._salary_extractor = SalarySlipExtractor()
        self._generic_extractor = GenericExtractor()

    def extract_data(self, input_data: ExtractorInput) -> StructuredBusinessDocument:
        """Selects extractor for document type and processes ParsedDocument."""
        start_time = time.perf_counter()
        doc_type = input_data.document_type
        parsed_doc = input_data.parsed_document

        try:
            logger.info("Extracting structured data for doc_id: %s | Type: %s", parsed_doc.document_id, doc_type)

            if doc_type in {DocumentType.SALES_INVOICE, DocumentType.PURCHASE_INVOICE, DocumentType.GST_INVOICE, DocumentType.CREDIT_NOTE, DocumentType.DEBIT_NOTE}:
                result = self._invoice_extractor.extract(parsed_doc, doc_type)
            elif doc_type in {DocumentType.PURCHASE_ORDER, DocumentType.QUOTATION, DocumentType.SALES_ORDER}:
                result = self._po_extractor.extract(parsed_doc, doc_type)
            elif doc_type == DocumentType.BANK_STATEMENT:
                result = self._bank_extractor.extract(parsed_doc, doc_type)
            elif doc_type in {DocumentType.RECEIPT, DocumentType.PAYMENT_VOUCHER, DocumentType.EXPENSE_BILL}:
                result = self._receipt_extractor.extract(parsed_doc, doc_type)
            elif doc_type == DocumentType.SALARY_SLIP:
                result = self._salary_extractor.extract(parsed_doc, doc_type)
            else:
                result = self._generic_extractor.extract(parsed_doc, doc_type)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result.metadata.processing_time_ms = round(elapsed_ms, 2)

            logger.info(
                "Structured extraction complete for doc_id: %s in %.2fms | Fields: %d",
                parsed_doc.document_id,
                result.metadata.processing_time_ms,
                result.metadata.extracted_fields_count,
            )

            return result

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Failed structured extraction for document '{parsed_doc.document_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ExtractorExecutionError(error_msg) from exc