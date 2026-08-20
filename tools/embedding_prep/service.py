"""Service responsible for converting validated documents into semantic content and chunks."""

import time
from typing import Any, Dict, List

from logger import logger
from tools.embedding_prep.constants import (
    META_KEY_CHUNK_INDEX,
    META_KEY_DOCUMENT_ID,
    META_KEY_DOCUMENT_TYPE,
    META_KEY_IS_VALID,
    META_KEY_TOTAL_CHUNKS,
    META_KEY_WORKSPACE_ID,
    SECTION_BUYER,
    SECTION_HEADER,
    SECTION_LINE_ITEMS,
    SECTION_RAW_PAGES,
    SECTION_SELLER,
    SECTION_SUMMARY,
    SECTION_TAXES,
    SECTION_TOTALS,
)
from tools.embedding_prep.exceptions import (
    ChunkingExecutionError,
    InvalidInputForPreparationError,
)
from tools.embedding_prep.models import (
    EmbeddingPrepInput,
    EmbeddingPrepMetadata,
    PreparedChunk,
    PreparedDocumentContent,
)
from tools.embedding_prep.utils import create_overlapping_chunks, generate_chunk_id


class EmbeddingPrepService:
    """Deterministic service transforming structured document models into semantic chunk streams."""

    def prepare_document(self, input_data: EmbeddingPrepInput) -> PreparedDocumentContent:
        """Formats structured business document into readable semantic text and creates chunks.

        Raises:
            InvalidInputForPreparationError: If input fields or workspace details are missing.
            ChunkingExecutionError: If execution fails unexpectedly during chunk creation.
        """
        struct_doc = input_data.structured_document
        if not struct_doc or not struct_doc.document_id:
            error_msg = "Invalid or missing StructuredBusinessDocument in EmbeddingPrepInput."
            logger.error(error_msg)
            raise InvalidInputForPreparationError(error_msg)

        if not input_data.workspace_id:
            error_msg = "Workspace ID is required for embedding preparation isolation."
            logger.error(error_msg)
            raise InvalidInputForPreparationError(error_msg)

        start_time = time.perf_counter()
        doc_id = struct_doc.document_id
        workspace_id = input_data.workspace_id
        doc_type = struct_doc.metadata.document_type

        try:
            logger.info("Preparing embedding content for doc_id: %s | Workspace: %s", doc_id, workspace_id)

            # 1. Build unified, clean semantic text representation
            full_text_blocks = self._build_semantic_blocks(input_data)
            full_semantic_text = "\n\n".join(full_text_blocks)

            # 2. Generate overlapping text chunks
            raw_chunks = create_overlapping_chunks(full_semantic_text)
            total_chunks = len(raw_chunks)

            # 3. Build PreparedChunk models with strict workspace/document metadata
            prepared_chunks: List[PreparedChunk] = []
            for idx, chunk_text in enumerate(raw_chunks):
                chunk_id = generate_chunk_id(doc_id, idx)
                
                chunk_metadata: Dict[str, Any] = {
                    META_KEY_WORKSPACE_ID: workspace_id,
                    META_KEY_DOCUMENT_ID: doc_id,
                    META_KEY_DOCUMENT_TYPE: doc_type,
                    META_KEY_CHUNK_INDEX: idx,
                    META_KEY_TOTAL_CHUNKS: total_chunks,
                    META_KEY_IS_VALID: input_data.is_valid,
                }

                prepared_chunks.append(
                    PreparedChunk(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        workspace_id=workspace_id,
                        chunk_index=idx,
                        text_content=chunk_text,
                        metadata=chunk_metadata,
                    )
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            prep_metadata = EmbeddingPrepMetadata(
                document_id=doc_id,
                workspace_id=workspace_id,
                document_type=doc_type,
                total_chunks=total_chunks,
                total_characters=len(full_semantic_text),
                processing_time_ms=round(elapsed_ms, 2),
            )

            result = PreparedDocumentContent(
                document_id=doc_id,
                workspace_id=workspace_id,
                document_type=doc_type,
                full_semantic_text=full_semantic_text,
                chunks=prepared_chunks,
                metadata=prep_metadata,
            )

            logger.info(
                "Embedding preparation completed for doc_id: %s in %.2fms | Total Chunks: %d",
                doc_id,
                prep_metadata.processing_time_ms,
                prep_metadata.total_chunks,
            )

            return result

        except InvalidInputForPreparationError:
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Error during embedding preparation for document '{doc_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ChunkingExecutionError(error_msg) from exc

    def _build_semantic_blocks(self, input_data: EmbeddingPrepInput) -> List[str]:
        """Converts structured document components into clean text paragraphs."""
        doc = input_data.structured_document
        blocks: List[str] = []

        # Document Summary Block
        blocks.append(
            f"=== {SECTION_SUMMARY} ===\n"
            f"Document Type: {doc.metadata.document_type}\n"
            f"Document ID: {doc.document_id}\n"
            f"Validation Status: {'Valid' if input_data.is_valid else 'Invalid/Has Warnings'}"
        )

        # Header Details
        header = doc.header
        header_lines = [f"=== {SECTION_HEADER} ==="]
        if header.document_number:
            header_lines.append(f"Number: {header.document_number}")
        if header.document_date:
            header_lines.append(f"Date: {header.document_date}")
        if header.due_date:
            header_lines.append(f"Due Date: {header.due_date}")
        if header.reference_number:
            header_lines.append(f"Reference PO/Ref: {header.reference_number}")
        if header.place_of_supply:
            header_lines.append(f"Place of Supply: {header.place_of_supply}")
        if len(header_lines) > 1:
            blocks.append("\n".join(header_lines))

        # Seller / Vendor Info
        seller = doc.seller
        seller_lines = [f"=== {SECTION_SELLER} ==="]
        if seller.name:
            seller_lines.append(f"Name: {seller.name}")
        if seller.gstin:
            seller_lines.append(f"GSTIN: {seller.gstin}")
        if seller.pan:
            seller_lines.append(f"PAN: {seller.pan}")
        if seller.address:
            seller_lines.append(f"Address: {seller.address}")
        if len(seller_lines) > 1:
            blocks.append("\n".join(seller_lines))

        # Buyer / Customer Info
        buyer = doc.buyer
        buyer_lines = [f"=== {SECTION_BUYER} ==="]
        if buyer.name:
            buyer_lines.append(f"Name: {buyer.name}")
        if buyer.gstin:
            buyer_lines.append(f"GSTIN: {buyer.gstin}")
        if buyer.pan:
            buyer_lines.append(f"PAN: {buyer.pan}")
        if buyer.address:
            buyer_lines.append(f"Address: {buyer.address}")
        if len(buyer_lines) > 1:
            blocks.append("\n".join(buyer_lines))

        # Line Items
        if doc.line_items:
            item_lines = [f"=== {SECTION_LINE_ITEMS} ==="]
            for item in doc.line_items:
                item_str = f"Item #{item.item_number or '-'}: {item.description or 'N/A'}"
                if item.quantity:
                    item_str += f" | Qty: {item.quantity}"
                if item.unit_price:
                    item_str += f" | Rate: {item.unit_price}"
                if item.amount:
                    item_str += f" | Amount: {item.amount}"
                item_lines.append(item_str)
            blocks.append("\n".join(item_lines))

        # Tax Details
        taxes = doc.taxes
        tax_lines = [f"=== {SECTION_TAXES} ==="]
        if taxes.cgst:
            tax_lines.append(f"CGST: {taxes.cgst}")
        if taxes.sgst:
            tax_lines.append(f"SGST: {taxes.sgst}")
        if taxes.igst:
            tax_lines.append(f"IGST: {taxes.igst}")
        if taxes.total_tax:
            tax_lines.append(f"Total Tax: {taxes.total_tax}")
        if len(tax_lines) > 1:
            blocks.append("\n".join(tax_lines))

        # Totals Details
        totals = doc.totals
        totals_lines = [f"=== {SECTION_TOTALS} ==="]
        if totals.subtotal:
            totals_lines.append(f"Subtotal: {totals.subtotal}")
        if totals.tax_amount:
            totals_lines.append(f"Total Tax: {totals.tax_amount}")
        if totals.grand_total:
            totals_lines.append(f"Grand Total: {totals.grand_total}")
        totals_lines.append(f"Currency: {totals.currency or 'INR'}")
        blocks.append("\n".join(totals_lines))

        # Supplementary Raw Pages from ParsedDocument if available
        parsed_doc = input_data.parsed_document
        if parsed_doc and parsed_doc.pages:
            raw_lines = [f"=== {SECTION_RAW_PAGES} ==="]
            for page in parsed_doc.pages:
                if page.text and page.text.strip():
                    raw_lines.append(f"[Page {page.page_number}]\n{page.text.strip()}")
            if len(raw_lines) > 1:
                blocks.append("\n".join(raw_lines))

        return blocks