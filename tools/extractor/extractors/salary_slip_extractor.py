"""Extractor for Salary Slips / Payslips."""

from typing import List
from tools.extractor.constants import PAN_REGEX
from tools.extractor.models import (
    DocumentTotals,
    ExtractionMetadata,
    HeaderFields,
    LineItem,
    PartyInformation,
    StructuredBusinessDocument,
)
from tools.parser.models import ParsedDocument


class SalarySlipExtractor:
    """Extracts employee earnings, deductions, and net pay from Salary Slips."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        text_corpus = "\n".join(p.text for p in parsed_doc.pages)
        pans = PAN_REGEX.findall(text_corpus)

        employee = PartyInformation(pan=pans[0] if pans else None)

        line_items: List[LineItem] = []
        for table in parsed_doc.tables:
            for idx, row in enumerate(table.rows, start=1):
                if row:
                    line_items.append(
                        LineItem(
                            item_number=idx,
                            description=row[0] if len(row) > 0 else "",
                            amount=row[-1] if len(row) > 1 else None,
                        )
                    )

        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len(line_items) + (1 if pans else 0),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            seller=employee,
            line_items=line_items,
            metadata=metadata,
        )