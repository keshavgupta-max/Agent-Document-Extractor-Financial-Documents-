"""Extractor for Bank Statements supporting heterogeneous column formats."""

import re
from typing import Any, Dict, List, Optional
from tools.extractor.models import (
    ExtractionMetadata,
    HeaderFields,
    LineItem,
    StructuredBusinessDocument,
)
from tools.parser.models import ParsedDocument, TableContent
CREDIT_ALIASES = {
    "credit",
    "credits",
    "credit amount",
    "credited",
    "deposit",
    "deposits",
    "deposit amount",
    "cr amount",
    "deposit (cr)",
    "deposit(cr)",
    "credit (cr)",
    "credit(cr)",
    "cr",
}

DEBIT_ALIASES = {
    "debit",
    "debits",
    "debit amount",
    "withdrawal",
    "withdrawals",
    "withdrawal amount",
    "dr amount",
    "withdrawal (dr)",
    "withdrawal(dr)",
    "debit (dr)",
    "debit(dr)",
    "dr",
}

BALANCE_ALIASES = {
    "balance",
    "closing balance",
    "available balance",
    "account balance",
    "running balance",
    "bal",
}

DIRECTION_ALIASES = {
    "type",
    "transaction type",
    "txn type",
    "cr/dr",
    "cr / dr",
    "dr/cr",
    "d/c",
    "c/d",
    "direction",
    "cr dr",
    "dr cr",
    "credit/debit",
}

AMOUNT_ALIASES = {
    "amount",
    "txn amount",
    "transaction amount",
    "amount (inr)",
    "net amount",
    "total amount",
    "amount(inr)",
    "amount in inr",
}

CREDIT_DIRECTION_VALUES = {"cr", "credit", "credited", "c", "deposit", "dep", "cr."}
DEBIT_DIRECTION_VALUES = {"dr", "db", "debit", "debited", "d", "withdrawal", "wd", "dr."}


def _normalize_header(header: str) -> str:
    """Normalizes header string for safe exact alias matching."""
    cleaned = header.strip().lower()
    cleaned = re.sub(r"[\._\-/]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _parse_amount(val_str: Optional[str]) -> Optional[float]:
    """Safely extracts a floating-point amount from string."""
    if not val_str or not val_str.strip():
        return None
    cleaned = re.sub(r"[^\d.-]", "", val_str.strip().replace(",", ""))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


class BankStatementExtractor:
    """Extracts account details, transaction rows, and statement aggregates from Bank Statements."""

    def extract(self, parsed_doc: ParsedDocument, doc_type: str) -> StructuredBusinessDocument:
        line_items: List[LineItem] = []
        additional_fields: Dict[str, Any] = {}

        total_credits = 0.0
        total_debits = 0.0
        valid_credit_count = 0
        valid_debit_count = 0
        has_credit_column = False
        has_debit_column = False
        total_transactions = 0
        item_counter = 0
        first_balance: Optional[str] = None
        last_balance: Optional[str] = None

        for table in parsed_doc.tables:
            raw_headers = [h.strip() for h in table.headers] if table.headers else []
            normalized_headers = [_normalize_header(h) for h in raw_headers]

            # Priority 1: Check for explicit Credit column
            credit_idx = next(
                (
                    i
                    for i, nh in enumerate(normalized_headers)
                    if nh in CREDIT_ALIASES
                    or (
                        any(
                            kw in nh.split()
                            for kw in ["credit", "credits", "deposit", "deposits", "credited"]
                        )
                        and "description" not in nh
                        and "narration" not in nh
                        and "particular" not in nh
                        and "remark" not in nh
                    )
                ),
                None,
            )
            if credit_idx is not None:
                has_credit_column = True

            # Priority 1: Check for explicit Debit column
            debit_idx = next(
                (
                    i
                    for i, nh in enumerate(normalized_headers)
                    if nh in DEBIT_ALIASES
                    or (
                        any(
                            kw in nh.split()
                            for kw in ["debit", "debits", "withdrawal", "withdrawals"]
                        )
                        and "description" not in nh
                        and "narration" not in nh
                        and "particular" not in nh
                        and "remark" not in nh
                    )
                ),
                None,
            )
            if debit_idx is not None:
                has_debit_column = True

            # Priority 2: Check for Direction (Type) and Amount columns ONLY if explicit columns absent
            direction_idx = None
            amount_idx = None
            if credit_idx is None and debit_idx is None:
                direction_idx = next(
                    (
                        i
                        for i, nh in enumerate(normalized_headers)
                        if nh in DIRECTION_ALIASES
                        and "mode" not in nh
                        and "channel" not in nh
                    ),
                    None,
                )
                amount_idx = next(
                    (
                        i
                        for i, nh in enumerate(normalized_headers)
                        if nh in AMOUNT_ALIASES
                        and "balance" not in nh
                        and "acc" not in nh
                        and "account" not in nh
                    ),
                    None,
                )

            # Resolve balance column
            balance_idx = next(
                (
                    i
                    for i, nh in enumerate(normalized_headers)
                    if nh in BALANCE_ALIASES or "balance" in nh.split()
                ),
                None,
            )

            for row in table.rows:
                if not row:
                    continue

                total_transactions += 1
                item_counter += 1

                # 1. Handle Explicit Credit Column
                if credit_idx is not None and credit_idx < len(row):
                    cr_val = _parse_amount(row[credit_idx])
                    if cr_val is not None and cr_val > 0:
                        total_credits += cr_val
                        valid_credit_count += 1

                # 2. Handle Explicit Debit Column
                if debit_idx is not None and debit_idx < len(row):
                    dr_val = _parse_amount(row[debit_idx])
                    if dr_val is not None and dr_val > 0:
                        total_debits += dr_val
                        valid_debit_count += 1

                # 3. Handle Type (Cr/Db) + Amount fallback
                if (
                    credit_idx is None
                    and debit_idx is None
                    and direction_idx is not None
                    and amount_idx is not None
                    and direction_idx < len(row)
                    and amount_idx < len(row)
                ):
                    dir_val = row[direction_idx].strip().lower()
                    amt_val = _parse_amount(row[amount_idx])
                    if amt_val is not None and amt_val > 0:
                        if dir_val in CREDIT_DIRECTION_VALUES:
                            total_credits += amt_val
                            valid_credit_count += 1
                            has_credit_column = True
                        elif dir_val in DEBIT_DIRECTION_VALUES:
                            total_debits += amt_val
                            valid_debit_count += 1
                            has_debit_column = True

                # Track opening/closing balances across tables
                if balance_idx is not None and balance_idx < len(row):
                    bal_str = row[balance_idx].strip()
                    if bal_str:
                        if first_balance is None:
                            first_balance = bal_str
                        last_balance = bal_str

                # Map column headers to values for LineItem description
                if raw_headers and len(raw_headers) == len(row):
                    row_parts = [
                        f"{raw_headers[i]}: {row[i].strip()}"
                        for i in range(len(row))
                        if row[i] and row[i].strip()
                    ]
                    narrative = " | ".join(row_parts) if row_parts else " | ".join(row)
                elif raw_headers:
                    row_parts = []
                    for i, val in enumerate(row):
                        val_str = val.strip() if val else ""
                        if not val_str:
                            continue
                        if i < len(raw_headers) and raw_headers[i]:
                            row_parts.append(f"{raw_headers[i]}: {val_str}")
                        else:
                            row_parts.append(val_str)
                    narrative = " | ".join(row_parts) if row_parts else " | ".join(row)
                else:
                    narrative = " | ".join(val.strip() for val in row if val and val.strip())

                line_items.append(
                    LineItem(
                        item_number=item_counter,
                        description=narrative,
                        amount=None,
                    )
                )

        if valid_credit_count > 0 or has_credit_column:
            additional_fields["total_credit_amount"] = f"{total_credits:.2f}"
        if valid_debit_count > 0 or has_debit_column:
            additional_fields["total_debit_amount"] = f"{total_debits:.2f}"

        additional_fields["total_transactions"] = total_transactions

        if first_balance is not None:
            additional_fields["opening_balance"] = first_balance
        if last_balance is not None:
            additional_fields["closing_balance"] = last_balance

        metadata = ExtractionMetadata(
            document_type=doc_type,
            extracted_fields_count=len(line_items) + len(additional_fields),
            tables_extracted=len(parsed_doc.tables),
        )

        return StructuredBusinessDocument(
            document_id=parsed_doc.document_id,
            header=HeaderFields(),
            line_items=line_items,
            additional_fields=additional_fields,
            metadata=metadata,
        )
