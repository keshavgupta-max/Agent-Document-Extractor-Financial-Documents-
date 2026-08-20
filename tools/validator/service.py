"""Single Validation Service coordinating business rule and math checks."""

import time
from typing import List
from logger import logger
from tools.extractor.models import StructuredBusinessDocument
from tools.validator.constants import (
    CALCULATION_TOLERANCE_AMOUNT,
    DocumentTypeGroup,
    RULE_MSG_GRAND_TOTAL_MISMATCH,
    RULE_MSG_INVALID_BUYER_GSTIN,
    RULE_MSG_INVALID_BUYER_PAN,
    RULE_MSG_INVALID_CURRENCY,
    RULE_MSG_INVALID_DATE_FORMAT,
    RULE_MSG_INVALID_SELLER_GSTIN,
    RULE_MSG_INVALID_SELLER_PAN,
    RULE_MSG_MISSING_DOC_DATE,
    RULE_MSG_MISSING_DOC_NO,
    RULE_MSG_MISSING_LINE_ITEMS,
    RULE_MSG_MISSING_SELLER_GSTIN,
    RULE_MSG_SUBTOTAL_MISMATCH,
    RULE_MSG_TAX_MISMATCH,
    SUPPORTED_CURRENCIES,
    ValidationSeverity,
    ValidationStatus,
)
from tools.validator.exceptions import InvalidStructuredDocumentError, ValidationExecutionError
from tools.validator.models import DocumentValidationResult, ValidationInput, ValidationIssue
from tools.validator.utils import (
    is_valid_gstin,
    is_valid_pan,
    normalize_string,
    parse_amount,
    parse_date,
)


class ValidationService:
    """Coordinating service that executes core validation logic across document structures."""

    def validate_document(self, input_data: ValidationInput) -> DocumentValidationResult:
        """Validates a structured document against business, party, tax, and math rules.

        Raises:
            InvalidStructuredDocumentError: If structured document payload is missing or invalid.
            ValidationExecutionError: If an unhandled runtime error occurs during validation.
        """
        doc = input_data.structured_document
        if not doc or not doc.document_id:
            error_msg = "Invalid StructuredBusinessDocument payload provided to ValidationService."
            logger.error(error_msg)
            raise InvalidStructuredDocumentError(error_msg)

        start_time = time.perf_counter()
        issues: List[ValidationIssue] = []
        doc_type = doc.metadata.document_type

        try:
            logger.info("Starting validation for doc_id: %s | Type: %s", doc.document_id, doc_type)

            # 1. Header Validation
            self._validate_header(doc, doc_type, issues)

            # 2. Party Information Validation
            self._validate_parties(doc, doc_type, issues)

            # 3. Line Items & Currency Validation
            self._validate_line_items_and_currency(doc, doc_type, issues)

            # 4. Mathematical Cross-Footing Checks
            self._validate_totals_and_taxes(doc, issues)

            # Aggregate statistics and status
            error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
            warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)

            is_valid = error_count == 0
            if is_valid:
                status = (
                    ValidationStatus.VALID_WITH_WARNINGS
                    if warning_count > 0
                    else ValidationStatus.VALID
                )
            else:
                status = ValidationStatus.INVALID

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = DocumentValidationResult(
                document_id=doc.document_id,
                document_type=doc_type,
                is_valid=is_valid,
                status=status,
                issues=issues,
                error_count=error_count,
                warning_count=warning_count,
                processing_time_ms=round(elapsed_ms, 2),
            )

            logger.info(
                "Validation completed for doc_id: %s in %.2fms | Valid: %s | Errors: %d | Warnings: %d",
                doc.document_id,
                result.processing_time_ms,
                result.is_valid,
                result.error_count,
                result.warning_count,
            )

            # Read-only diagnostic logging to expose failing validation issue(s)
            if result.issues:
                for idx, issue in enumerate(result.issues, 1):
                    logger.warning(
                        "Validation Issue #%d | Rule: %s | Field: %s | Severity: %s | Message: %s",
                        idx,
                        issue.rule_id,
                        issue.field,
                        issue.severity,
                        issue.message,
                    )

            return result

        except InvalidStructuredDocumentError:
            raise
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Error validating document '{doc.document_id}': {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ValidationExecutionError(error_msg) from exc

    def _validate_header(
        self, doc: StructuredBusinessDocument, doc_type: str, issues: List[ValidationIssue]
    ) -> None:
        """Validates presence and format of core header fields."""
        if doc_type in DocumentTypeGroup.HEADER_REQUIRED:
            if not normalize_string(doc.header.document_number):
                issues.append(
                    ValidationIssue(
                        rule_id="VAL_HDR_001",
                        severity=ValidationSeverity.ERROR,
                        field="header.document_number",
                        message=RULE_MSG_MISSING_DOC_NO,
                    )
                )

            date_str = normalize_string(doc.header.document_date)
            if not date_str:
                issues.append(
                    ValidationIssue(
                        rule_id="VAL_HDR_002",
                        severity=ValidationSeverity.ERROR,
                        field="header.document_date",
                        message=RULE_MSG_MISSING_DOC_DATE,
                    )
                )
            elif parse_date(date_str) is None:
                issues.append(
                    ValidationIssue(
                        rule_id="VAL_HDR_003",
                        severity=ValidationSeverity.WARNING,
                        field="header.document_date",
                        message=RULE_MSG_INVALID_DATE_FORMAT.format(date_str=date_str),
                    )
                )

    def _validate_parties(
        self, doc: StructuredBusinessDocument, doc_type: str, issues: List[ValidationIssue]
    ) -> None:
        """Validates seller/buyer GSTIN and PAN formats."""
        seller_gstin = normalize_string(doc.seller.gstin)
        buyer_gstin = normalize_string(doc.buyer.gstin)
        seller_pan = normalize_string(doc.seller.pan)
        buyer_pan = normalize_string(doc.buyer.pan)

        if doc_type in DocumentTypeGroup.TAX_REQUIRED and not seller_gstin:
            issues.append(
                ValidationIssue(
                    rule_id="VAL_PRT_001",
                    severity=ValidationSeverity.WARNING,
                    field="seller.gstin",
                    message=RULE_MSG_MISSING_SELLER_GSTIN.format(doc_type=doc_type),
                )
            )

        if seller_gstin and not is_valid_gstin(seller_gstin):
            issues.append(
                ValidationIssue(
                    rule_id="VAL_PRT_002",
                    severity=ValidationSeverity.ERROR,
                    field="seller.gstin",
                    message=RULE_MSG_INVALID_SELLER_GSTIN.format(gstin=seller_gstin),
                )
            )

        if buyer_gstin and not is_valid_gstin(buyer_gstin):
            issues.append(
                ValidationIssue(
                    rule_id="VAL_PRT_003",
                    severity=ValidationSeverity.ERROR,
                    field="buyer.gstin",
                    message=RULE_MSG_INVALID_BUYER_GSTIN.format(gstin=buyer_gstin),
                )
            )

        if seller_pan and not is_valid_pan(seller_pan):
            issues.append(
                ValidationIssue(
                    rule_id="VAL_PRT_004",
                    severity=ValidationSeverity.WARNING,
                    field="seller.pan",
                    message=RULE_MSG_INVALID_SELLER_PAN.format(pan=seller_pan),
                )
            )

        if buyer_pan and not is_valid_pan(buyer_pan):
            issues.append(
                ValidationIssue(
                    rule_id="VAL_PRT_005",
                    severity=ValidationSeverity.WARNING,
                    field="buyer.pan",
                    message=RULE_MSG_INVALID_BUYER_PAN.format(pan=buyer_pan),
                )
            )

    def _validate_line_items_and_currency(
        self, doc: StructuredBusinessDocument, doc_type: str, issues: List[ValidationIssue]
    ) -> None:
        """Validates item presence and ISO currency code."""
        if doc_type in DocumentTypeGroup.INVOICE_FAMILY and not doc.line_items:
            issues.append(
                ValidationIssue(
                    rule_id="VAL_ITM_001",
                    severity=ValidationSeverity.ERROR,
                    field="line_items",
                    message=RULE_MSG_MISSING_LINE_ITEMS.format(doc_type=doc_type),
                )
            )

        currency = normalize_string(doc.totals.currency)
        if currency and currency.upper() not in SUPPORTED_CURRENCIES:
            issues.append(
                ValidationIssue(
                    rule_id="VAL_CUR_001",
                    severity=ValidationSeverity.WARNING,
                    field="totals.currency",
                    message=RULE_MSG_INVALID_CURRENCY.format(currency=currency),
                )
            )

    def _validate_totals_and_taxes(
        self, doc: StructuredBusinessDocument, issues: List[ValidationIssue]
    ) -> None:
        """Cross-foots line items sum against subtotal, taxes, and grand total."""
        stated_subtotal = parse_amount(doc.totals.subtotal)
        stated_grand_total = parse_amount(doc.totals.grand_total)
        stated_tax_amount = parse_amount(doc.totals.tax_amount)

        cgst = parse_amount(doc.taxes.cgst) or 0.0
        sgst = parse_amount(doc.taxes.sgst) or 0.0
        igst = parse_amount(doc.taxes.igst) or 0.0

        # Calculate line item sum
        calculated_line_sum = 0.0
        has_valid_line_amounts = False
        for item in doc.line_items:
            item_amt = parse_amount(item.amount)
            if item_amt is not None:
                calculated_line_sum += item_amt
                has_valid_line_amounts = True

        # Subtotal verification
        if stated_subtotal is not None and has_valid_line_amounts:
            if abs(calculated_line_sum - stated_subtotal) > CALCULATION_TOLERANCE_AMOUNT:
                issues.append(
                    ValidationIssue(
                        rule_id="VAL_MTH_001",
                        severity=ValidationSeverity.WARNING,
                        field="totals.subtotal",
                        message=RULE_MSG_SUBTOTAL_MISMATCH.format(
                            calculated=calculated_line_sum, stated=stated_subtotal
                        ),
                    )
                )

        # Tax total verification
        calculated_tax_sum = cgst + sgst + igst
        if stated_tax_amount is not None and (cgst > 0 or sgst > 0 or igst > 0):
            if abs(calculated_tax_sum - stated_tax_amount) > CALCULATION_TOLERANCE_AMOUNT:
                issues.append(
                    ValidationIssue(
                        rule_id="VAL_MTH_002",
                        severity=ValidationSeverity.WARNING,
                        field="totals.tax_amount",
                        message=RULE_MSG_TAX_MISMATCH.format(
                            calculated=calculated_tax_sum, stated=stated_tax_amount
                        ),
                    )
                )

        # Grand Total verification
        effective_subtotal = stated_subtotal if stated_subtotal is not None else calculated_line_sum
        effective_tax = stated_tax_amount if stated_tax_amount is not None else calculated_tax_sum
        expected_grand_total = effective_subtotal + effective_tax

        if stated_grand_total is not None and (effective_subtotal > 0 or effective_tax > 0):
            if abs(expected_grand_total - stated_grand_total) > CALCULATION_TOLERANCE_AMOUNT:
                issues.append(
                    ValidationIssue(
                        rule_id="VAL_MTH_003",
                        severity=ValidationSeverity.ERROR,
                        field="totals.grand_total",
                        message=RULE_MSG_GRAND_TOTAL_MISMATCH.format(
                            stated=stated_grand_total, calculated=expected_grand_total
                        ),
                    )
                )