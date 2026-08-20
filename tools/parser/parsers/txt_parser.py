"""Text (.txt) Document Parser using Python standard utilities."""

from logger import logger
from tools.parser.exceptions import CorruptedDocument, ParserExecutionError
from tools.parser.models import PageContent, ParsedDocument


class TxtParser:
    """Parser dedicated to extracting raw text content from Plain Text (.txt) files."""
    

    def parse(
        self,
        file_bytes: bytes,
        document_id: str,
        storage_path: str,
        mime_type: str = "text/plain",
    ) -> ParsedDocument:
        """Decodes text bytes and converts plain text content into a normalized PageContent object.

        Raises:
            CorruptedDocument: If the text bytes cannot be decoded.
            ParserExecutionError: If an error occurs during parsing.
        """
        try:
            # Attempt decoding with UTF-8, fallback to latin-1
            try:
                decoded_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                decoded_text = file_bytes.decode("latin-1")
        except Exception as exc:
            error_msg = f"Failed to parse TXT document (decoding error): {str(exc)}"
            logger.error(error_msg)
            raise CorruptedDocument(error_msg) from exc

        try:
            pages = [PageContent(page_number=1, text=decoded_text)]
            tables = []

            metadata = {
                "character_count": len(decoded_text),
                "line_count": len(decoded_text.splitlines()),
            }

            return ParsedDocument(
                document_id=document_id,
                storage_path=storage_path,
                file_extension=".txt",
                mime_type=mime_type,
                page_count=1,
                pages=pages,
                tables=tables,
                metadata=metadata,
                parsing_status="SUCCESS",
            )

        except Exception as exc:
            error_msg = f"Error processing TXT content for document {document_id}: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ParserExecutionError(error_msg) from exc