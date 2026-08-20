"""Common regular expressions and keyword constants for structured data extraction."""

import re
from typing import Pattern

# Regex for Indian GSTIN (15 characters)
GSTIN_REGEX: Pattern[str] = re.compile(
    r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b",
    re.IGNORECASE,
)

# Regex for PAN Number (10 characters)
PAN_REGEX: Pattern[str] = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    re.IGNORECASE,
)

# Common Date Formats (e.g., DD/MM/YYYY, YYYY-MM-DD, DD-MMM-YYYY)
DATE_REGEX: Pattern[str] = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
    re.IGNORECASE,
)

# Currency and Monetary Amount Regex (e.g., 1,234.56 or 1234.56 or Rs. 500)
AMOUNT_REGEX: Pattern[str] = re.compile(
    r"(?:Rs\.?|INR|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?)",
    re.IGNORECASE,
)

# Email address pattern
EMAIL_REGEX: Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
)

# Phone number pattern (Indian/International formats)
PHONE_REGEX: Pattern[str] = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
)

# Standard document field keywords
INVOICE_NO_KEYWORDS = ["INVOICE NO", "INVOICE NUMBER", "INV NO", "BILL NO", "INVOICE #"]
PO_NO_KEYWORDS = ["PO NO", "PO NUMBER", "PURCHASE ORDER NO", "P.O. REF"]
DATE_KEYWORDS = ["DATE", "INVOICE DATE", "BILL DATE", "DOCUMENT DATE", "STATEMENT DATE"]
DUE_DATE_KEYWORDS = ["DUE DATE", "PAYMENT DUE"]
TOTAL_KEYWORDS = ["TOTAL", "GRAND TOTAL", "NET AMOUNT", "NET PAYABLE", "BALANCE DUE"]
SUBTOTAL_KEYWORDS = ["SUBTOTAL", "SUB TOTAL", "TAXABLE VALUE", "TAXABLE AMOUNT"]
TAX_KEYWORDS = ["TAX AMOUNT", "TOTAL TAX", "GST AMOUNT", "CGST", "SGST", "IGST"]