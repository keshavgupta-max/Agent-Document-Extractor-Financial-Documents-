"""Fallback extractor for untyped or generic business documents."""

from typing import List, Optional
from tools.extractor.constants import DATE_REGEX, EMAIL_REGEX, GSTIN_REGEX, PAN_REGEX, PHONE_REGEX
from tools.extractor.models import (
    DocumentTotals,
    ExtractionMetadata,
    HeaderFields,
    LineItem,
    PartyInformation,
    PaymentInformation,
    StructuredBusinessDocument,
    TaxInformation,
)
from tools.parser.models import ParsedDocument


class GenericExtractor:
    """Basic extraction strategy for unclassified or general documents using key patterns."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        text_corpus = "\n".join(p.text for p in parsed_doc.pages)

        # Extract basic pattern matches
        gstins = GSTIN_REGEX.findall(text_corpus)
        pans = PAN_REGEX.findall(text_corpus)
        dates = DATE_REGEX.findall(text_corpus)
        emails = EMAIL_REGEX.findall(text_corpus)
        phones = PHONE_REGEX.findall(text_corpus)

        seller = PartyInformation(
            gstin=gstins[0] if gstins else None,
            pan=pans[0] if pans else None,
            email=emails[0] if emails else None,
            phone=phones[0] if phones else None,
        )

        header = HeaderFields(
            document_date=dates[0] if dates else None,
        )

        line_items: List[LineItem] = []
        for table in parsed_doc.tables:
            for idx, row in enumerate(table.rows, start=1):
                if row:
                    line_items.append(
                        LineItem(
                            item_number=idx,
                            description=" | ".join(row),
                        )
                    )

        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len(gstins) + len(dates) + len(line_items),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            header=header,
            seller=seller,
            line_items=line_items,
            metadata=metadata,
        )