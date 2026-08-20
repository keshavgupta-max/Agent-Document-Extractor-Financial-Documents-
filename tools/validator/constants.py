"""Constants, enums, regex patterns, and default tolerances for document validation."""

import re
from typing import Pattern, Set


class DocumentTypeGroup:
    """Groupings of DocumentType enums for clean business logic checks."""

    INVOICE_FAMILY: Set[str] = {
        "Sales Invoice",
        "Purchase Invoice",
        "GST Invoice",
        "Credit Note",
        "Debit Note",
    }

    ORDER_FAMILY: Set[str] = {
        "Purchase Order",
        "Quotation",
        "Sales Order",
    }

    HEADER_REQUIRED: Set[str] = {
        "Sales Invoice",
        "Purchase Invoice",
        "GST Invoice",
        "Purchase Order",
        "Quotation",
        "Sales Order",
        "Delivery Challan",
    }

    TAX_REQUIRED: Set[str] = {
        "GST Invoice",
        "Sales Invoice",
        "Purchase Invoice",
    }


class ValidationSeverity:
    """Severity levels for document validation issues."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationStatus:
    """Overall document validation status."""

    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"


# Tolerances and Financial Thresholds
CALCULATION_TOLERANCE_AMOUNT: float = 0.05  # Floating point tolerance (e.g. 5 paise)
MINIMUM_VALID_AMOUNT: float = 0.0
LINE_ITEM_MIN_QTY: float = 0.0

# Supported Currencies
SUPPORTED_CURRENCIES: Set[str] = {"INR", "USD", "EUR", "GBP", "AED"}

# Supported Date Formats for Parsing
SUPPORTED_DATE_FORMATS: list[str] = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
]

# Regex Patterns
GSTIN_REGEX_PATTERN: Pattern[str] = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$",
    re.IGNORECASE,
)

PAN_REGEX_PATTERN: Pattern[str] = re.compile(
    r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
    re.IGNORECASE,
)

IFSC_REGEX_PATTERN: Pattern[str] = re.compile(
    r"^[A-Z]{4}0[A-Z0-9]{6}$",
    re.IGNORECASE,
)

# Rule Message Templates & Descriptions
RULE_MSG_MISSING_DOC_NO = "Document number is missing or blank."
RULE_MSG_MISSING_DOC_DATE = "Document issuance date is missing or invalid."
RULE_MSG_INVALID_DATE_FORMAT = "Document date '{date_str}' is not in a recognized date format."
RULE_MSG_MISSING_SELLER_GSTIN = "Seller GSTIN is required for {doc_type} but missing."
RULE_MSG_INVALID_SELLER_GSTIN = "Seller GSTIN '{gstin}' is invalid."
RULE_MSG_INVALID_BUYER_GSTIN = "Buyer GSTIN '{gstin}' is invalid."
RULE_MSG_INVALID_SELLER_PAN = "Seller PAN '{pan}' is invalid."
RULE_MSG_INVALID_BUYER_PAN = "Buyer PAN '{pan}' is invalid."
RULE_MSG_MISSING_LINE_ITEMS = "At least one line item is required for {doc_type}."
RULE_MSG_INVALID_CURRENCY = "Unrecognized or unsupported currency code '{currency}'."
RULE_MSG_SUBTOTAL_MISMATCH = "Subtotal mismatch: Calculated line items sum ({calculated:.2f}) does not equal stated subtotal ({stated:.2f})."
RULE_MSG_TAX_MISMATCH = "Tax total mismatch: Calculated sum of CGST/SGST/IGST ({calculated:.2f}) does not equal stated tax amount ({stated:.2f})."
RULE_MSG_GRAND_TOTAL_MISMATCH = "Grand total mismatch: Stated total ({stated:.2f}) does not equal Subtotal + Taxes ({calculated:.2f})."