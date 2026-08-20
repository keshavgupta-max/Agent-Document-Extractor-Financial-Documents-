"""Extractor for Receipts and Payment Vouchers."""

import re
from typing import List, Optional
from tools.extractor.constants import DATE_KEYWORDS, TOTAL_KEYWORDS
from tools.extractor.models import (
    DocumentTotals,
    ExtractionMetadata,
    HeaderFields,
    PaymentInformation,
    StructuredBusinessDocument,
)
from tools.parser.models import ParsedDocument


class ReceiptExtractor:
    """Extracts payment details from Receipts and Vouchers."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        text_corpus = "\n".join(p.text for p in parsed_doc.pages)
        lines = [line.strip() for line in text_corpus.splitlines() if line.strip()]

        rec_date = self._find_value_by_keywords(lines, DATE_KEYWORDS)
        amount = self._find_value_by_keywords(lines, TOTAL_KEYWORDS)

        header = HeaderFields(document_date=rec_date)
        totals = DocumentTotals(grand_total=amount)

        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len([v for v in [rec_date, amount] if v]),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            header=header,
            totals=totals,
            metadata=metadata,
        )

    def _find_value_by_keywords(self, lines: List[str], keywords: List[str]) -> Optional[str]:
        for line in lines:
            line_upper = line.upper()
            for kw in keywords:
                if kw in line_upper:
                    parts = re.split(r"[:\-=]", line, maxsplit=1)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
        return None