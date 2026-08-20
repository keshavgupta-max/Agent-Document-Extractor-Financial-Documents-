"""Extractor for Sales and Purchase Invoices."""

import re
from typing import List, Optional
from tools.extractor.constants import (
    DATE_KEYWORDS,
    DATE_REGEX,
    DUE_DATE_KEYWORDS,
    GSTIN_REGEX,
    INVOICE_NO_KEYWORDS,
    PAN_REGEX,
    SUBTOTAL_KEYWORDS,
    TOTAL_KEYWORDS,
)
from tools.extractor.models import (
    DocumentTotals,
    ExtractionMetadata,
    HeaderFields,
    LineItem,
    PartyInformation,
    StructuredBusinessDocument,
    TaxInformation,
)
from tools.parser.models import ParsedDocument


class InvoiceExtractor:
    """Extracts structured header, party, tax, and line-item details from Invoices."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        text_corpus = "\n".join(p.text for p in parsed_doc.pages)
        lines = [line.strip() for line in text_corpus.splitlines() if line.strip()]

        # 1. Header Extraction
        doc_num = self._find_value_by_keywords(lines, INVOICE_NO_KEYWORDS)
        doc_date = self._find_value_by_keywords(lines, DATE_KEYWORDS)
        if not doc_date:
            dates = DATE_REGEX.findall(text_corpus)
            doc_date = dates[0] if dates else None

        due_date = self._find_value_by_keywords(lines, DUE_DATE_KEYWORDS)

        header = HeaderFields(
            document_number=doc_num,
            document_date=doc_date,
            due_date=due_date,
        )

        # 2. Party Information
        gstins = GSTIN_REGEX.findall(text_corpus)
        pans = PAN_REGEX.findall(text_corpus)

        seller = PartyInformation(
            gstin=gstins[0] if len(gstins) > 0 else None,
            pan=pans[0] if len(pans) > 0 else None,
        )
        buyer = PartyInformation(
            gstin=gstins[1] if len(gstins) > 1 else None,
            pan=pans[1] if len(pans) > 1 else None,
        )

        # 3. Line Items from Tables
        line_items: List[LineItem] = []
        for table in parsed_doc.tables:
            for idx, row in enumerate(table.rows, start=1):
                if row:
                    line_items.append(
                        LineItem(
                            item_number=idx,
                            description=row[0] if len(row) > 0 else "",
                            quantity=row[1] if len(row) > 1 else None,
                            unit_price=row[2] if len(row) > 2 else None,
                            amount=row[-1] if len(row) > 3 else None,
                        )
                    )

        # 4. Totals & Tax Extraction
        subtotal = self._find_value_by_keywords(lines, SUBTOTAL_KEYWORDS)
        grand_total = self._find_value_by_keywords(lines, TOTAL_KEYWORDS)

        cgst = self._find_value_by_keywords(lines, ["CGST"])
        sgst = self._find_value_by_keywords(lines, ["SGST"])
        igst = self._find_value_by_keywords(lines, ["IGST"])

        total_tax: Optional[str] = None
        tax_components = [v for v in [cgst, sgst, igst] if v is not None]
        if tax_components:
            sum_tax = 0.0
            for val in tax_components:
                cleaned = re.sub(r"[^\d.]", "", val)
                try:
                    sum_tax += float(cleaned)
                except ValueError:
                    pass
            total_tax = f"{sum_tax:.2f}"

        taxes = TaxInformation(
            cgst=cgst,
            sgst=sgst,
            igst=igst,
            total_tax=total_tax,
        )

        totals = DocumentTotals(
            subtotal=subtotal,
            tax_amount=total_tax,
            grand_total=grand_total,
        )

        extracted_values = [doc_num, doc_date, subtotal, grand_total, cgst, sgst, igst, total_tax]
        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len([v for v in extracted_values if v]) + len(line_items),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            header=header,
            seller=seller,
            buyer=buyer,
            line_items=line_items,
            taxes=taxes,
            totals=totals,
            metadata=metadata,
        )

    def _find_value_by_keywords(self, lines: List[str], keywords: List[str]) -> Optional[str]:
        for line in lines:
            line_upper = line.upper()
            for kw in keywords:
                pattern = r"(?<![A-Z0-9])" + re.escape(kw) + r"(?![A-Z0-9])"
                if re.search(pattern, line_upper):
                    parts = re.split(r"[:\-=]", line, maxsplit=1)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()
        return None