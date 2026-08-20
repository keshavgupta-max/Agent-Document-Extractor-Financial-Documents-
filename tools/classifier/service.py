"""Classifier Service orchestrating document classification over ParsedDocument."""

import time
from logger import logger
from tools.classifier.constants import DocumentType, MINIMUM_CONFIDENCE_THRESHOLD
from tools.classifier.exceptions import ClassificationFailedError, InvalidParsedDocumentError
from tools.classifier.models import ClassifierInput, DocumentClassification
from tools.classifier.rules import RuleEngine


class ClassifierService:
    """Service responsible for evaluating business document types deterministically."""

    def classify_document(self, input_data: ClassifierInput) -> DocumentClassification:
        """Evaluates a ParsedDocument against business rules and assigns a document type.

        Raises:
            InvalidParsedDocumentError: If the input ParsedDocument is missing or empty.
            ClassificationFailedError: If an error occurs during classification evaluation.
        """
        parsed_doc = input_data.parsed_document
        if not parsed_doc or not parsed_doc.document_id:
            error_msg = "Invalid ParsedDocument provided to ClassifierService."
            logger.error(error_msg)
            raise InvalidParsedDocumentError(error_msg)

        start_time = time.perf_counter()

        try:
            logger.info("Classifying document_id: %s", parsed_doc.document_id)

            # Evaluate rules deterministically
            doc_type, confidence, matched_signals, reason = RuleEngine.evaluate(parsed_doc)

            # Fallback to UNKNOWN if score is below the minimum threshold
            if confidence < MINIMUM_CONFIDENCE_THRESHOLD:
                logger.info(
                    "Classification confidence %.2f below threshold %.2f for doc_id: %s. Defaulting to Unknown Document.",
                    confidence,
                    MINIMUM_CONFIDENCE_THRESHOLD,
                    parsed_doc.document_id,
                )
                doc_type = DocumentType.UNKNOWN
                reason = f"Confidence score ({confidence}) was below minimum threshold ({MINIMUM_CONFIDENCE_THRESHOLD})."

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            classification = DocumentClassification(
                document_id=parsed_doc.document_id,
                document_type=doc_type,
                confidence=confidence,
                matched_rules=matched_signals,
                reason=reason,
                processing_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                "Document %s classified as '%s' with confidence %.2f in %.2fms",
                parsed_doc.document_id,
                classification.document_type,
                classification.confidence,
                classification.processing_time_ms,
            )

            return classification

        except InvalidParsedDocumentError:
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Failed to classify document '{parsed_doc.document_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ClassificationFailedError(error_msg) from exc