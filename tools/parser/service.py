"""Parser Service responsible for selecting and invoking format-specific parsers."""

import time
from typing import Optional

from logger import logger
from storage.base_storage import BaseStorage
from storage.local_storage import LocalStorage
from tools.parser.constants import PARSER_EXTENSION_MAP, ParsingStatus
from tools.parser.exceptions import (
    DocumentNotFound,
    EmptyDocument,
    ParserExecutionError,
    UnsupportedDocumentType,
)
from tools.parser.models import ParsedDocument, ParserInput
from tools.parser.parsers import (
    CSVParser,
    DOCXParser,
    ExcelParser,
    ImageParser,
    PDFParser,
    TXTParser,
)


class ParserService:
    """Service that reads files from storage and delegates parsing to format parsers."""

    def __init__(self, storage_manager: Optional[BaseStorage] = None) -> None:
        self._storage = storage_manager or LocalStorage()
        self._pdf_parser = PDFParser()
        self._docx_parser = DOCXParser()
        self._excel_parser = ExcelParser()
        self._csv_parser = CSVParser()
        self._txt_parser = TXTParser()
        self._image_parser = ImageParser()

    def parse_document(self, input_data: ParserInput) -> ParsedDocument:
        """Reads stored file bytes, routes to the appropriate parser, and tracks duration.

        Raises:
            DocumentNotFound: If file is missing in storage.
            UnsupportedDocumentType: If file extension is not mapped to a parser.
            EmptyDocument: If stored file content is zero bytes.
            ParserExecutionError: If parsing execution fails.
        """
        # 1. Check storage existence
        if not self._storage.file_exists(input_data.storage_path):
            error_msg = f"Document not found at storage path: '{input_data.storage_path}'"
            logger.error(error_msg)
            raise DocumentNotFound(error_msg)

        # 2. Determine parser type based on normalized extension
        ext = input_data.file_extension.lower()
        parser_type = PARSER_EXTENSION_MAP.get(ext)

        if not parser_type:
            error_msg = f"Unsupported document extension for parsing: '{ext}'"
            logger.error(error_msg)
            raise UnsupportedDocumentType(error_msg)

        # 3. Read raw file bytes
        file_bytes = self._storage.get_file(input_data.storage_path)
        if not file_bytes or len(file_bytes) == 0:
            error_msg = f"Document at '{input_data.storage_path}' is empty (0 bytes)."
            logger.error(error_msg)
            raise EmptyDocument(error_msg)

        start_time = time.perf_counter()
        mime = input_data.mime_type or "application/octet-stream"

        try:
            logger.info(
                "Starting parsing for doc_id: %s | Type: %s | Path: %s",
                input_data.document_id,
                parser_type,
                input_data.storage_path,
            )

            if parser_type == "PDF":
                parsed_doc = self._pdf_parser.parse(
                    file_bytes=file_bytes,
                    document_id=input_data.document_id,
                    storage_path=input_data.storage_path,
                    mime_type=mime,
                )
            elif parser_type == "DOCX":
                parsed_doc = self._docx_parser.parse(
                    file_bytes=file_bytes,
                    document_id=input_data.document_id,
                    storage_path=input_data.storage_path,
                    mime_type=mime,
                )
            elif parser_type == "EXCEL":
                parsed_doc = self._excel_parser.parse(
                    file_bytes=file_bytes,
                    document_id=input_data.document_id,
                    storage_path=input_data.storage_path,
                    mime_type=mime,
                )
            elif parser_type == "CSV":
                parsed_doc = self._csv_parser.parse(
                    file_bytes=file_bytes,
                    document_id=input_data.document_id,
                    storage_path=input_data.storage_path,
                    mime_type=mime,
                )
            elif parser_type == "TXT":
                parsed_doc = self._txt_parser.parse(
                    file_bytes=file_bytes,
                    document_id=input_data.document_id,
                    storage_path=input_data.storage_path,
                    mime_type=mime,
                )
            elif parser_type == "IMAGE":
                parsed_doc = self._image_parser.parse(
                    file_bytes=file_bytes,
                    document_id=input_data.document_id,
                    storage_path=input_data.storage_path,
                    file_extension=ext,
                    mime_type=mime,
                )
            else:
                raise UnsupportedDocumentType(f"No parser available for type '{parser_type}'")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            parsed_doc.parsing_time_ms = round(elapsed_ms, 2)

            logger.info(
                "Successfully parsed doc_id: %s in %.2fms | Pages: %d | Tables: %d",
                input_data.document_id,
                parsed_doc.parsing_time_ms,
                parsed_doc.page_count,
                len(parsed_doc.tables),
            )

            return parsed_doc

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            if isinstance(exc, (UnsupportedDocumentType, DocumentNotFound, EmptyDocument)):
                raise
            error_msg = f"Failed to parse document '{input_data.document_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ParserExecutionError(error_msg) from exc