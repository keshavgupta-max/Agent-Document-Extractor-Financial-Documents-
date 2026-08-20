"""CSV Document Parser using standard csv module."""

import csv
import io
from logger import logger
from tools.parser.exceptions import CorruptedDocument, ParserExecutionError
from tools.parser.models import PageContent, ParsedDocument, TableContent


class CSVParser:
    """Parser dedicated to extracting rows and columns from Comma-Separated Values (.csv) files."""

    def parse(
        self,
        file_bytes: bytes,
        document_id: str,
        storage_path: str,
        mime_type: str = "text/csv",
    ) -> ParsedDocument:
        """Extracts tabular records and converts CSV rows into normalized page and table content.

        Raises:
            CorruptedDocument: If the CSV bytes cannot be decoded or parsed.
            ParserExecutionError: If an error occurs during parsing.
        """
        try:
            # Attempt decoding with utf-8, fallback to latin-1 for legacy encodings
            try:
                decoded_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                decoded_content = file_bytes.decode("latin-1")

            stream = io.StringIO(decoded_content)
            reader = csv.reader(stream)
            rows = [row for row in reader if any(row)]
        except Exception as exc:
            error_msg = f"Failed to parse CSV document (corrupted or invalid encoding): {str(exc)}"
            logger.error(error_msg)
            raise CorruptedDocument(error_msg) from exc

        try:
            if not rows:
                pages = [PageContent(page_number=1, text="")]
                tables = []
            else:
                headers = [str(cell).strip() for cell in rows[0]]
                data_rows = [
                    [str(cell).strip() for cell in row] for row in rows[1:]
                ]

                # Construct textual summary for full-text indexing/search
                text_lines = [" | ".join(headers)]
                for row in data_rows:
                    text_lines.append(" | ".join(row))
                csv_text = "\n".join(text_lines)

                pages = [PageContent(page_number=1, text=csv_text)]
                tables = [
                    TableContent(
                        table_index=0,
                        page_number=1,
                        headers=headers,
                        rows=data_rows,
                    )
                ]

            metadata = {
                "total_rows": len(rows),
            }

            return ParsedDocument(
                document_id=document_id,
                storage_path=storage_path,
                file_extension=".csv",
                mime_type=mime_type,
                page_count=1,
                pages=pages,
                tables=tables,
                metadata=metadata,
                parsing_status="SUCCESS",
            )

        except Exception as exc:
            error_msg = f"Error processing CSV content for document {document_id}: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ParserExecutionError(error_msg) from exc