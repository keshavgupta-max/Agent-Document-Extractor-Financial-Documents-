"""Image Document Parser using Pillow (PIL). Extracts metadata ONLY (No OCR)."""

import io
from PIL import Image

from logger import logger
from tools.parser.exceptions import CorruptedDocument, ParserExecutionError
from tools.parser.models import ImageMetadata, PageContent, ParsedDocument


class ImageParser:
    """Parser dedicated to extracting metadata from image files (.png, .jpg, .jpeg).

    Does NOT perform OCR. Content extraction is left to downstream vision components.
    """

    def parse(
        self,
        file_bytes: bytes,
        document_id: str,
        storage_path: str,
        file_extension: str = ".png",
        mime_type: str = "image/png",
    ) -> ParsedDocument:
        """Extracts width, height, format, and dimensions from raw image bytes.

        Raises:
            CorruptedDocument: If the image cannot be identified or opened by PIL.
            ParserExecutionError: If an error occurs during metadata processing.
        """
        try:
            image_stream = io.BytesIO(file_bytes)
            with Image.open(image_stream) as img:
                width, height = img.size
                image_format = img.format or file_extension.lstrip(".").upper()
        except Exception as exc:
            error_msg = f"Failed to open image file (corrupted or unsupported format): {str(exc)}"
            logger.error(error_msg)
            raise CorruptedDocument(error_msg) from exc

        try:
            image_meta = ImageMetadata(
                width=width,
                height=height,
                format=image_format,
                size_bytes=len(file_bytes),
            )

            # Informative text placeholder for downstream processing pipeline
            pages = [
                PageContent(
                    page_number=1,
                    text=f"[IMAGE FILE: {image_format} ({width}x{height}px)]",
                )
            ]

            metadata = {
                "width": width,
                "height": height,
                "format": image_format,
            }

            return ParsedDocument(
                document_id=document_id,
                storage_path=storage_path,
                file_extension=file_extension,
                mime_type=mime_type,
                page_count=1,
                pages=pages,
                tables=[],
                image_metadata=image_meta,
                metadata=metadata,
                parsing_status="SUCCESS",
            )

        except Exception as exc:
            error_msg = f"Error extracting image metadata for document {document_id}: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ParserExecutionError(error_msg) from exc