"""Extractor for Purchase Orders and Quotations."""

import re
from typing import List, Optional
from tools.extractor.constants import DATE_KEYWORDS, GSTIN_REGEX, PO_NO_KEYWORDS, TOTAL_KEYWORDS
from tools.extractor.models import (
    DocumentTotals,
    ExtractionMetadata,
    HeaderFields,
    LineItem,
    PartyInformation,
    StructuredBusinessDocument,
)
from tools.parser.models import ParsedDocument


class PurchaseOrderExtractor:
    """Extracts structured fields from Purchase Orders and Quotations."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        text_corpus = "\n".join(p.text for p in parsed_doc.pages)
        lines = [line.strip() for line in text_corpus.splitlines() if line.strip()]

        po_number = self._find_value_by_keywords(lines, PO_NO_KEYWORDS)
        po_date = self._find_value_by_keywords(lines, DATE_KEYWORDS)

        header = HeaderFields(
            document_number=po_number,
            document_date=po_date,
        )

        gstins = GSTIN_REGEX.findall(text_corpus)
        seller = PartyInformation(gstin=gstins[0] if gstins else None)

        line_items: List[LineItem] = []
        for table in parsed_doc.tables:
            for idx, row in enumerate(table.rows, start=1):
                if row:
                    line_items.append(
                        LineItem(
                            item_number=idx,
                            description=row[0] if len(row) > 0 else "",
                            quantity=row[1] if len(row) > 1 else None,
                            amount=row[-1] if len(row) > 2 else None,
                        )
                    )

        total_val = self._find_value_by_keywords(lines, TOTAL_KEYWORDS)
        totals = DocumentTotals(grand_total=total_val)

        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len([v for v in [po_number, po_date, total_val] if v]) + len(line_items),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            header=header,
            seller=seller,
            line_items=line_items,
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