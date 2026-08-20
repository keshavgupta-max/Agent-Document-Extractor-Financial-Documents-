"""Reusable normalization, parsing, and regex validation helper functions."""

import re
from datetime import datetime
from typing import Optional

from tools.validator.constants import (
    GSTIN_REGEX_PATTERN,
    IFSC_REGEX_PATTERN,
    PAN_REGEX_PATTERN,
    SUPPORTED_DATE_FORMATS,
)


def normalize_string(val: Optional[str]) -> Optional[str]:
    """Cleans and strips whitespace from raw extracted string inputs."""
    if val is None:
        return None
    cleaned = str(val).strip()
    return cleaned if cleaned else None


def parse_amount(val: Optional[str]) -> Optional[float]:
    """Extracts floating point numerical value from currency strings (e.g. 'Rs. 1,234.50' -> 1234.50)."""
    if val is None:
        return None
    cleaned = re.sub(r"[^\d.-]", "", str(val).replace(",", ""))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Attempts to parse raw date string using standard project date formats."""
    cleaned = normalize_string(date_str)
    if not cleaned:
        return None

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def is_valid_gstin(gstin: Optional[str]) -> bool:
    """Validates 15-character Indian GSTIN against official format regex."""
    cleaned = normalize_string(gstin)
    if not cleaned:
        return False
    return bool(GSTIN_REGEX_PATTERN.match(cleaned))


def is_valid_pan(pan: Optional[str]) -> bool:
    """Validates 10-character Indian PAN against standard format regex."""
    cleaned = normalize_string(pan)
    if not cleaned:
        return False
    return bool(PAN_REGEX_PATTERN.match(cleaned))


def is_valid_ifsc(ifsc: Optional[str]) -> bool:
    """Validates Indian Bank IFSC code against standard format regex."""
    cleaned = normalize_string(ifsc)
    if not cleaned:
        return False
    return bool(IFSC_REGEX_PATTERN.match(cleaned))