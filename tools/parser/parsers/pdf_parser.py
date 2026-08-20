"""PDF Document Parser using PyMuPDF (fitz)."""

import fitz  # PyMuPDF
from logger import logger
from tools.parser.exceptions import CorruptedDocument, ParserExecutionError
from tools.parser.models import PageContent, ParsedDocument, TableContent


class PDFParser:
    """Parser dedicated to extracting text, metadata, and tables from PDF documents."""

    def parse(
        self,
        file_bytes: bytes,
        document_id: str,
        storage_path: str,
        mime_type: str = "application/pdf",
    ) -> ParsedDocument:
        """Extracts pages, text, basic metadata, and tables from raw PDF bytes.

        Raises:
            CorruptedDocument: If the PDF cannot be opened or parsed.
            ParserExecutionError: If an unhandled exception occurs during extraction.
        """
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            error_msg = f"Failed to open PDF document (corrupted or invalid): {str(exc)}"
            logger.error(error_msg)
            raise CorruptedDocument(error_msg) from exc

        pages = []
        tables = []
        table_idx = 0

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                page_number = page_num + 1

                pages.append(PageContent(page_number=page_number, text=text))

                # Extract tables if PyMuPDF table finder is available
                try:
                    tabs = page.find_tables()
                    if tabs and tabs.tables:
                        for tab in tabs.tables:
                            matrix = tab.extract()
                            if matrix and len(matrix) > 0:
                                headers = [str(cell or "").strip() for cell in matrix[0]]
                                rows = [
                                    [str(cell or "").strip() for cell in row]
                                    for row in matrix[1:]
                                ]
                                tables.append(
                                    TableContent(
                                        table_index=table_idx,
                                        page_number=page_number,
                                        headers=headers,
                                        rows=rows,
                                    )
                                )
                                table_idx += 1
                except Exception as tab_exc:
                    logger.debug(
                        "Table extraction skipped on page %d for doc %s: %s",
                        page_number,
                        document_id,
                        str(tab_exc),
                    )

            # Metadata extraction
            raw_meta = doc.metadata or {}
            metadata = {
                "author": raw_meta.get("author", ""),
                "title": raw_meta.get("title", ""),
                "subject": raw_meta.get("subject", ""),
                "creator": raw_meta.get("creator", ""),
                "producer": raw_meta.get("producer", ""),
            }

            page_count = len(doc)
            doc.close()

            return ParsedDocument(
                document_id=document_id,
                storage_path=storage_path,
                file_extension=".pdf",
                mime_type=mime_type,
                page_count=page_count,
                pages=pages,
                tables=tables,
                metadata=metadata,
                parsing_status="SUCCESS",
            )

        except Exception as exc:
            doc.close()
            error_msg = f"Error extracting PDF content for document {document_id}: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ParserExecutionError(error_msg) from exc