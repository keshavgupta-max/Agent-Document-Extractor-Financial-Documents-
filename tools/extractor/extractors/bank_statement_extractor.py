"""Extractor for Bank Statements."""

from typing import List
from tools.extractor.models import (
    ExtractionMetadata,
    HeaderFields,
    LineItem,
    PartyInformation,
    PaymentInformation,
    StructuredBusinessDocument,
)
from tools.parser.models import ParsedDocument


class BankStatementExtractor:
    """Extracts account details and transaction rows from Bank Statements."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        line_items: List[LineItem] = []

        # Iterate over transaction tables
        for table in parsed_doc.tables:
            for idx, row in enumerate(table.rows, start=1):
                if row:
                    narrative = " | ".join(row)
                    line_items.append(
                        LineItem(
                            item_number=idx,
                            description=narrative,
                            amount=row[-1] if len(row) > 0 else None,
                        )
                    )

        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len(line_items),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            header=HeaderFields(),
            line_items=line_items,
            metadata=metadata,
        )